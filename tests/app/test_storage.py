#!/usr/bin/env python

from app.storage import TempStorage, DataNotFoundError, InstanceIdMismatchError, UserIdMismatchError
from unittest import TestCase, main


class TempSorageTestCase(TestCase):
    def setUp(self):
        self.storage = TempStorage()
        self.input_string = 'The quick brown fox jumps over the lazy dog'

    def tearDown(self):
        del self.storage

    def test_input_without_chat_without_user_output_without_chat_without_user(self):
        uid = self.storage.add(self.input_string)
        output = self.storage.pop(uid)
        self.assertEqual(self.input_string, output)

    def test_input_with_chat_without_user_output_with_same_chat_without_user(self):
        uid = self.storage.add(self.input_string, chat="chat1")
        output = self.storage.pop(uid, chat="chat1")
        self.assertEqual(self.input_string, output)

    def test_input_without_chat_with_user_output_without_chat_with_same_user(self):
        uid = self.storage.add(self.input_string, user="user1")
        output = self.storage.pop(uid, user="user1")
        self.assertEqual(self.input_string, output)

    def test_input_with_chat_with_user_output_with_same_chat_with_same_user(self):
        uid = self.storage.add(self.input_string, chat="chat1", user="user1")
        output = self.storage.pop(uid, chat="chat1", user="user1")
        self.assertEqual(self.input_string, output)

    def test_input_with_chat_without_user_output_with_other_chat_without_user(self):
        uid = self.storage.add(self.input_string, chat="chat1")
        with self.assertRaises(InstanceIdMismatchError):
            self.storage.pop(uid, chat="chat2")

    def test_input_without_chat_with_user_output_without_chat_with_other_user(self):
        uid = self.storage.add(self.input_string, user="user1")
        with self.assertRaises(UserIdMismatchError):
            self.storage.pop(uid, user="user2")

    def test_input_with_chat_with_user_output_with_same_chat_with_other_user(self):
        uid = self.storage.add(self.input_string, chat="chat1", user="user1")
        with self.assertRaises(UserIdMismatchError):
            self.storage.pop(uid, chat="chat1", user="user2")

    def test_input_with_chat_with_user_output_with_other_chat_with_same_user(self):
        uid = self.storage.add(self.input_string, chat="chat1", user="user1")
        with self.assertRaises(InstanceIdMismatchError):
            self.storage.pop(uid, chat="chat2", user="user1")

    def test_input_with_chat_with_user_output_with_other_chat_with_other_user(self):
        uid = self.storage.add(self.input_string, chat="chat1", user="user1")
        with self.assertRaises(InstanceIdMismatchError):
            self.storage.pop(uid, chat="chat2", user="user2")

    def test_batch_input_without_chat_without_user_output_without_chat_without_user(self):
        with self.storage.batch() as batch:
            uid = batch.add(self.input_string)
        output = self.storage.pop(uid)
        self.assertEqual(self.input_string, output)

    def test_batch_with_chat_without_user_output_with_same_chat_without_user(self):
        with self.storage.batch(chat="chat1") as batch:
            uid = batch.add(self.input_string)
        output = self.storage.pop(uid, chat="chat1")
        self.assertEqual(self.input_string, output)

    def test_batch_input_without_chat_with_user_output_without_chat_with_same_user(self):
        with self.storage.batch(user="user1") as batch:
            uid = batch.add(self.input_string)
        output = self.storage.pop(uid, user="user1")
        self.assertEqual(self.input_string, output)

    def test_batch_input_with_chat_with_user_output_with_same_chat_with_same_user(self):
        with self.storage.batch(chat="chat1", user="user1") as batch:
            uid = batch.add(self.input_string)
        output = self.storage.pop(uid, chat="chat1", user="user1")
        self.assertEqual(self.input_string, output)

    def test_batch_input_with_chat_without_user_output_with_other_chat_without_user(self):
        with self.storage.batch(chat="chat1") as batch:
            uid = batch.add(self.input_string)
        with self.assertRaises(InstanceIdMismatchError):
            self.storage.pop(uid, chat="chat2")

    def test_batch_input_without_chat_with_user_output_without_chat_with_other_user(self):
        with self.storage.batch(user="user1") as batch:
            uid = batch.add(self.input_string)
        with self.assertRaises(UserIdMismatchError):
            self.storage.pop(uid, user="user2")

    def test_batch_input_with_chat_with_user_output_with_same_chat_with_other_user(self):
        with self.storage.batch(chat="chat1", user="user1") as batch:
            uid = batch.add(self.input_string)
        with self.assertRaises(UserIdMismatchError):
            self.storage.pop(uid, chat="chat1", user="user2")

    def test_batch_input_with_chat_with_user_output_with_other_chat_with_same_user(self):
        with self.storage.batch(chat="chat1", user="user1") as batch:
            uid = batch.add(self.input_string)
        with self.assertRaises(InstanceIdMismatchError):
            self.storage.pop(uid, chat="chat2", user="user1")

    def test_batch_input_with_chat_with_user_output_with_other_chat_with_other_user(self):
        with self.storage.batch(chat="chat1", user="user1") as batch:
            uid = batch.add(self.input_string)
        with self.assertRaises(InstanceIdMismatchError):
            self.storage.pop(uid, chat="chat2", user="user2")

    def test_batch_removing_after_adding(self):
        with self.storage.batch(chat="chat1", user="user1") as batch:
            uid1 = batch.add(self.input_string)
            uid2 = batch.add(self.input_string)
        output = self.storage.pop(uid1, chat="chat1", user="user1")
        self.assertEqual(self.input_string, output)
        with self.assertRaises(DataNotFoundError):
            self.storage.pop(uid2, chat="chat1", user="user1")


if __name__ == "__main__":
    pass
