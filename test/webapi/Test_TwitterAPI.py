from pathlib import Path
import sys
import unittest
from contextlib import ExitStack

import orjson
from mock import MagicMock, patch

from personaltwilog.webapi.TwitterAPI import TwitterAPI
from personaltwilog.webapi.valueobject.ScreenName import ScreenName
from personaltwilog.webapi.valueobject.Token import Token
from personaltwilog.webapi.valueobject.UserId import UserId
from personaltwilog.webapi.valueobject.UserName import UserName


class TestTwitterAPI(unittest.TestCase):

    def get_instance(self) -> TwitterAPI:
        authorize_screen_name = "authorize_screen_name"
        ct0 = "ct0"
        auth_token = "auth_token"
        return TwitterAPI(authorize_screen_name, ct0, auth_token)

    def get_json_dict(self) -> dict:
        return orjson.loads(Path("./test/cache/users_sample.json").read_bytes())

    def test_init(self):
        authorize_screen_name = "authorize_screen_name"
        ct0 = "ct0"
        auth_token = "auth_token"
        actual = TwitterAPI(authorize_screen_name, ct0, auth_token)
        self.assertEqual(ScreenName(authorize_screen_name), actual.authorize_screen_name)
        self.assertEqual(Token.create(authorize_screen_name, ct0, auth_token), actual.token)

    def test_scraper(self):
        with ExitStack() as stack:
            mock_scraper = stack.enter_context(patch("personaltwilog.webapi.TwitterAPI.Scraper"))
            twitter = self.get_instance()
            mock_scraper.side_effect = lambda cookies, pbar, debug: "scraper_instance"

            actual = twitter.scraper
            self.assertEqual("scraper_instance", actual)
            mock_scraper.assert_called_once_with(
                cookies={"ct0": twitter.token.ct0, "auth_token": twitter.token.auth_token}, pbar=False, debug=0
            )
            mock_scraper.reset_mock(side_effect=True)

            actual = twitter.scraper
            self.assertEqual("scraper_instance", actual)
            mock_scraper.assert_not_called()

    def test_find_values(self):
        twitter = self.get_instance()
        json_dict = self.get_json_dict()

        actual = twitter._find_values(json_dict, "rest_id")
        self.assertEqual(["12345678"], actual)
        actual = twitter._find_values(json_dict, "name")
        self.assertEqual(["dummy_user_name"], actual)
        actual = twitter._find_values(json_dict, "screen_name")
        self.assertEqual(["dummy_screen_name"], actual)

        actual = twitter._find_values(json_dict, "no_included_key")
        self.assertEqual([], actual)
        actual = twitter._find_values("invalid_object", "rest_id")
        self.assertEqual([], actual)

    def test_get_user(self):
        with ExitStack() as stack:
            mock_scraper = stack.enter_context(patch("personaltwilog.webapi.TwitterAPI.Scraper"))
            twitter = self.get_instance()
            json_dict = self.get_json_dict()
            mock_scraper.return_value.users.side_effect = lambda screen_names: json_dict["data"]["user"]

            screen_name = "dummy_screen_name"
            actual = twitter._get_user(screen_name)
            self.assertEqual(json_dict["data"]["user"], actual)
            self.assertEqual(True, hasattr(twitter, "_user_dict"))
            self.assertEqual(json_dict["data"]["user"], twitter._user_dict[screen_name])
            mock_scraper.return_value.users.assert_called_once_with([screen_name])
            mock_scraper.return_value.users.reset_mock()

            actual = twitter._get_user(screen_name)
            self.assertEqual(json_dict["data"]["user"], actual)
            self.assertEqual(True, hasattr(twitter, "_user_dict"))
            self.assertEqual(json_dict["data"]["user"], twitter._user_dict[screen_name])
            mock_scraper.return_value.users.assert_not_called()

    def test_get_user_id(self):
        with ExitStack() as stack:
            mock_get_user = stack.enter_context(patch("personaltwilog.webapi.TwitterAPI.TwitterAPI._get_user"))
            twitter = self.get_instance()
            json_dict = self.get_json_dict()
            mock_get_user.side_effect = lambda screen_name: json_dict["data"]["user"]

            screen_name = "dummy_screen_name"
            actual = twitter.get_user_id(screen_name)
            expect = UserId(12345678)
            self.assertEqual(expect, actual)
            mock_get_user.assert_called_once_with(screen_name)

    def test_get_user_name(self):
        with ExitStack() as stack:
            mock_get_user = stack.enter_context(patch("personaltwilog.webapi.TwitterAPI.TwitterAPI._get_user"))
            twitter = self.get_instance()
            json_dict = self.get_json_dict()
            mock_get_user.side_effect = lambda screen_name: json_dict["data"]["user"]

            screen_name = "dummy_screen_name"
            actual = twitter.get_user_name(screen_name)
            expect = UserName("dummy_user_name")
            self.assertEqual(expect, actual)
            mock_get_user.assert_called_once_with(screen_name)

    def test_get_likes(self):
        with ExitStack() as stack:
            # mockcp = stack.enter_context(patch("configparser.ConfigParser"))
            pass

    def test_get_user_timeline(self):
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
