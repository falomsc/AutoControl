import re
import time
from typing import Dict

from pywinauto.application import Application
from pywinauto import mouse, clipboard, keyboard


class SoapTalker:
    """
    nedd to set check_params first to judge 4G or 5G
    """
    TX1 = 1
    TX2 = 2
    TX3 = 3
    TX4 = 4

    def __init__(self, path: str):
        app = Application(backend="uia").connect(path=path)
        soap_dlg = app.window(title="SoapTalker")
        # need to modify
        self.message = soap_dlg.children()[12].children()[2].children()[0].children()[0]
        self.text = soap_dlg.children()[13].children()[1].children()[0].children()[0]
        self.button_save = soap_dlg.children()[13].children()[1].children()[1]

        self.flag_5g = False
        self._rf_params = None

    def set_message_position(self):
        x = self.message.rectangle().left
        y = self.message.rectangle().top
        if not self.flag_5g:
            mouse.scroll(coords=(x + 100, y + 70), wheel_dist=8)
            mouse.click(coords=(x + 100, y + 70))
        else:
            mouse.scroll(coords=(x + 65, y + 145), wheel_dist=8)
            mouse.scroll(coords=(x + 65, y + 145), wheel_dist=8)
            mouse.click(coords=(x + 65, y + 145))

    def set_text_position(self):
        x = self.text.rectangle().left
        y = self.text.rectangle().top
        mouse.click(coords=(x + 50, y + 50))

    def send_message(self, delay=2):
        keyboard.send_keys('{VK_APPS}')
        keyboard.send_keys('{DOWN}')
        keyboard.send_keys('{ENTER}')
        time.sleep(delay)

    def message_init(self):
        self.set_message_position()
        for i in range(7):
            self.send_message()
            if not self.flag_5g:
                if i in (0, 2):
                    keyboard.send_keys('{DOWN}')
                else:
                    keyboard.send_keys('{DOWN 2}')
            else:
                if i == 1:
                    keyboard.send_keys('{DOWN}')
                else:
                    keyboard.send_keys('{DOWN 2}')

    def tx_on(self, tx_type, delay=3):
        self.set_message_position()
        if not self.flag_5g:
            keyboard.send_keys('{DOWN %d}' % (9+4*tx_type))
        else:
            keyboard.send_keys('{DOWN %d}' % (26 + 4 * tx_type))
        self.send_message()
        time.sleep(delay)
        keyboard.send_keys('{UP}')
        self.send_message()

    def tx_off(self, tx_type):
        self.set_message_position()
        if not self.flag_5g:
            keyboard.send_keys('{DOWN %d}' % (10+4*tx_type))
        else:
            keyboard.send_keys('{DOWN %d}' % (27 + 4 * tx_type))
        self.send_message()
        keyboard.send_keys('{DOWN}')
        self.send_message()

    def show_outline(self):
        self.message.draw_outline(colour='green', thickness=4)
        self.text.draw_outline(colour='blue', thickness=4)
        self.button_save.draw_outline(colour='red', thickness=4)

    # TODO another way
    def chang_tx_property(self, tx_type, freq, bandwidth):
        self.set_message_position()
        if self.flag_5g:
            keyboard.send_keys('{DOWN %d}' % (9 + 4 * tx_type))
        else:
            keyboard.send_keys('{DOWN %d}' % (26 + 4 * tx_type))
        self.set_text_position()
        keyboard.send_keys('^a^c')
        keyboard.send_keys('{BACKSPACE}')
        data = clipboard.GetData()
        re1 = re.compile("(?P<First><frequency>)(\d+)(?P<Second></frequency>.+?<bandwidth>)(\d+)(?P<Third></bandwidth>)", flags=re.S)
        r1 = re.sub(re1, r'\g<First>%d\g<Second>%d\g<Third>' % (freq*10e6, bandwidth*10e6), data)
        keyboard.send_keys(r1, pause=0.01, with_spaces=True, with_tabs=True, with_newlines=True)
        self.button_save.click_input()

    @property
    def check_params(self) -> bool:
        return self._rf_params

    @check_params.setter
    def check_params(self, rf_params: Dict[str, str]) -> None:
        if rf_params.get('branch') in ('0', '1', '2', '3'):
            self.flag_5g = True
        elif rf_params.get('branch') in ('4', '5', '6', '7'):
            self.flag_5g = False
        self._rf_params = rf_params