# RandTalkBot Bot matching you with a random person on Telegram.
# Copyright (C) 2016 quasiyoke
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio
import asynctest
from randtalkbot.stranger_handler import StrangerHandler, MissingCommandError, UnsupportedContentError
from asynctest.mock import patch, Mock, MagicMock, CoroutineMock

class TestStrangerHandler(asynctest.TestCase):
    def setUp(self):
        self.stranger = CoroutineMock()
        self.stranger_service = Mock()
        self.stranger_service.get_or_create_stranger.return_value = self.stranger
        initial_msg = {
            'chat': {
                'id': 31416,
                }
            }
        self.stranger_handler = StrangerHandler((Mock(), initial_msg, 31416), self.stranger_service)

    @asynctest.ignore_loop
    def test_init(self):
        self.assertEqual(self.stranger_handler._stranger_service, self.stranger_service)
        self.assertEqual(self.stranger_handler._stranger, self.stranger)
        self.stranger_service.get_or_create_stranger.assert_called_once_with(31416, self.stranger_handler)

    @asynctest.ignore_loop
    def test_get_command(self):
        self.assertEqual(StrangerHandler._get_command('/begin chat'), 'begin')
        self.assertEqual(StrangerHandler._get_command('/start'), 'start')
        with self.assertRaises(MissingCommandError):
            StrangerHandler._get_command('/beginnnnnn')

    @asynctest.ignore_loop
    def test_get_content_kwargs__text(self):
        content_kwargs = StrangerHandler._get_content_kwargs(
            {'text': 'foo'},
            'text',
            )
        self.assertEqual(
            content_kwargs,
            {'text': 'foo'},
            )

    @asynctest.ignore_loop
    def test_get_content_kwargs__text_with_reply(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs(
                {
                    'text': 'foo',
                    'reply_to_message': None
                    },
                'text',
                )

    @asynctest.ignore_loop
    def test_get_content_kwargs__invalid_text(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs({}, 'text')

    @asynctest.ignore_loop
    def test_get_content_kwargs__photo(self):
        content_kwargs = StrangerHandler._get_content_kwargs(
            {
                'photo': [
                    {'file_id': 'foo'},
                    {'file_id': 'bar'},
                    ],
                },
            'photo',
            )
        self.assertEqual(
            content_kwargs,
            {'photo': 'bar'},
            )

    @asynctest.ignore_loop
    def test_get_content_kwargs__photo_with_caption(self):
        content_kwargs = StrangerHandler._get_content_kwargs(
            {
                'caption': 'baz',
                'photo': [
                    {'file_id': 'foo'},
                    {'file_id': 'bar'},
                    ],
                },
            'photo',
            )
        self.assertEqual(
            content_kwargs,
            {
                'caption': 'baz',
                'photo': 'bar',
                },
            )

    @asynctest.ignore_loop
    def test_get_content_kwargs__photo_with_reply(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs(
                {
                    'reply_to_message': None,
                    'photo': [
                        {'file_id': 'foo'},
                        {'file_id': 'bar'},
                        ],
                    },
                'photo',
                )

    @asynctest.ignore_loop
    def test_get_content_kwargs__invalid_photo(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs({}, 'photo')

    @asynctest.ignore_loop
    def test_get_content_kwargs__video(self):
        with self.assertRaises(UnsupportedContentError):
            StrangerHandler._get_content_kwargs({}, 'video')

    def test_handle_command__begin(self):
        self.stranger_service.set_partner = CoroutineMock()
        yield from self.stranger_handler._handle_command('begin')
        self.stranger_service.set_partner.assert_called_once_with(self.stranger)

    def test_handle_command__begin_error(self):
        from randtalkbot.stranger_service import PartnerObtainingError
        self.stranger_service.set_partner = CoroutineMock(side_effect=PartnerObtainingError())
        yield from self.stranger_handler._handle_command('begin')
        self.stranger_service.set_partner.assert_not_called()

    def test_handle_command__end(self):
        yield from self.stranger_handler._handle_command('end')
        self.stranger.end_chatting.assert_called_once_with()

    @patch('randtalkbot.stranger_handler.HELP_PATTERN', 'help {0}')
    @asyncio.coroutine
    def test_handle_command__help(self):
        self.stranger_handler.send_notification = CoroutineMock()
        yield from self.stranger_handler._handle_command('help')
        self.stranger_handler.send_notification.assert_called_once_with('help 31416')

    @patch('randtalkbot.stranger_handler.HELP_PATTERN', 'help {0}')
    @asyncio.coroutine
    def test_handle_command__start(self):
        self.stranger_handler.send_notification = CoroutineMock()
        yield from self.stranger_handler._handle_command('start')
        self.stranger_handler.send_notification.assert_called_once_with('help 31416')

    @patch('randtalkbot.stranger_handler.HELP_PATTERN', 'help {0}')
    @asyncio.coroutine
    def test_send_notification(self):
        self.stranger_handler.sender.sendMessage = CoroutineMock()
        yield from self.stranger_handler.send_notification('foo')
        self.stranger_handler.sender.sendMessage.assert_called_once_with(
            '*Rand Talk:* foo',
            parse_mode='Markdown',
            )

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @asyncio.coroutine
    def test_on_message__not_private(self):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'text', 'not_private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        yield from self.stranger_handler.on_message('message')
        telepot.glance2.assert_called_once_with('message')
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs',
        Mock(side_effect=UnsupportedContentError()),
        )
    @asyncio.coroutine
    def test_on_message__video(self):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'video', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        yield from self.stranger_handler.on_message('message')
        telepot.glance2.assert_called_once_with('message')
        self.stranger_handler.send_notification.assert_called_once_with(
            'Messages of this type weren\'t supported.',
            )
        self.stranger.send_to_partner.assert_not_called()
        StrangerHandler._get_content_kwargs.assert_called_once_with('message', 'video')

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_command',
        Mock(side_effect=MissingCommandError()),
        )
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__text(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'text', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        message = {
            'text': 'message_text',
            }
        StrangerHandler._get_content_kwargs.return_value = 'content_kwargs'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_called_once_with('text', 'content_kwargs')
        StrangerHandler._get_command.assert_called_once_with('message_text')
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'text')
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_command',
        Mock(side_effect=MissingCommandError()),
        )
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__text_no_partner(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.stranger import MissingPartnerError
        telepot.glance2.return_value = 'text', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        message = {
            'text': 'message_text',
            }
        self.stranger.send_to_partner = CoroutineMock(side_effect=MissingPartnerError())
        StrangerHandler._get_content_kwargs.return_value = 'content_kwargs'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_called_once_with('text', 'content_kwargs')
        StrangerHandler._get_command.assert_called_once_with('message_text')
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'text')
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_command', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__command(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'text', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        message = {
            'text': 'some_command',
            }
        StrangerHandler._get_command.return_value = 'some_command'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_not_called()
        StrangerHandler._get_command.assert_called_once_with('some_command')
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'text')
        handle_command_mock.assert_called_once_with('some_command')

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_command',
        Mock(side_effect=MissingCommandError()),
        )
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__photo(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        telepot.glance2.return_value = 'photo', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        message = {
            'photo': [
                {'file_id': 'foo'},
                {'file_id': 'bar'},
                ],
            }
        StrangerHandler._get_content_kwargs.return_value = 'content_kwargs'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_called_once_with('photo', 'content_kwargs')
        StrangerHandler._get_command.assert_not_called()
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'photo')
        handle_command_mock.assert_not_called()

    @patch('randtalkbot.stranger_handler.telepot', Mock())
    @patch(
        'randtalkbot.stranger_handler.StrangerHandler._get_command',
        Mock(side_effect=MissingCommandError()),
        )
    @patch('randtalkbot.stranger_handler.StrangerHandler._get_content_kwargs', Mock())
    @patch('randtalkbot.stranger_handler.StrangerHandler._handle_command')
    @asyncio.coroutine
    def test_on_message__photo_no_partner(self, handle_command_mock):
        from randtalkbot.stranger_handler import telepot
        from randtalkbot.stranger import MissingPartnerError
        telepot.glance2.return_value = 'photo', 'private', 31416
        self.stranger_handler.send_notification = CoroutineMock()
        message = {
            'photo': [
                {'file_id': 'foo'},
                {'file_id': 'bar'},
                ],
            }
        self.stranger.send_to_partner = CoroutineMock(side_effect=MissingPartnerError())
        StrangerHandler._get_content_kwargs.return_value = 'content_kwargs'
        yield from self.stranger_handler.on_message(message)
        telepot.glance2.assert_called_once_with(message)
        self.stranger_handler.send_notification.assert_not_called()
        self.stranger.send_to_partner.assert_called_once_with('photo', 'content_kwargs')
        StrangerHandler._get_command.assert_not_called()
        StrangerHandler._get_content_kwargs.assert_called_once_with(message, 'photo')
        handle_command_mock.assert_not_called()

    def test_send__text(self):
        self.stranger_handler.sender.sendMessage = CoroutineMock()
        content_kwargs = {'foo': 'bar'}
        yield from self.stranger_handler.send('text', content_kwargs)
        self.stranger_handler.sender.sendMessage.assert_called_once_with(**content_kwargs)

    def test_send__video(self):
        content_kwargs = {'foo': 'bar'}
        with self.assertRaises(UnsupportedContentError):
            yield from self.stranger_handler.send('video', content_kwargs)
