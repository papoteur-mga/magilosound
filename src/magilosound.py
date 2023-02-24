'''
Tool to configure sound backend

License: LGPLv2+

Authors:  Angelo Naselli <anaselli@linux.it>
Authors:  Papoteur

'''

import manatools.ui.basedialog as basedialog
import manatools.ui.common as common
import manatools.version as manatools
import manatools.services as mnservices
import yui
import gettext
import os.path
import subprocess
import rpm
import psutil
import logging


######################################################################
## 
## Main Dialog
## 
######################################################################


class SoundDialog(basedialog.BaseDialog):
    def __init__(self):
        basedialog.BaseDialog.__init__(self, "Sound configuration", "/usr/lib/libDrakX/icons/draksound-16.png", basedialog.DialogType.POPUP, 60, 15)
        self.pulse = self.is_pulse_installed()
        self.services_object = mnservices.Services()
        self._list_services = self.services_object.service_info
    
    def install(self, packages):
        # check if the package is installed first
        to_install = []
        if not hasattr(self, 'ts'):
            self.ts = rpm.TransactionSet()
        for p in packages:
            package_present = False
            mi = self.ts.dbMatch("name", p)
            for h in mi:
                package_present = True
                break
            if not package_present:
                to_install.append(p)
        if len(to_install) != 0:
            subprocess.run(["pkexec", "urpmi", "--auto"] + to_install)
    def uninstall(self, packages):
        # check if the package is installed first
        logging.debug(f"Uninstalling {packages}")
        to_uninstall = []
        ts = rpm.TransactionSet()
        for p in packages:
            package_present = False
            logging.debug(f"Look for {p}")
            mi = ts.dbMatch("name", p)
            for h in mi:
                logging.debug(h["name"])
                package_present = True
                break
            if package_present:
                to_uninstall.append(p)
        if len(to_uninstall) != 0:
            subprocess.run(["pkexec", "urpme", "--auto"] + to_uninstall)
        else:
            logging.debug("No package found to uninstall")

    def process_running(self):
        proc_iter = psutil.process_iter(attrs=["pid", "name"])
        sound_apps = ["pulseaudio", 
                      "pipewire",
                      "pipewire-media-session",
                      "wireplumber"]
        running = []
        for p in proc_iter:
            if (p.info["name"] in sound_apps) and not (p.info["name"] in running):
                running.append(p.info["name"])
        list_process = ""
        if len(running) > 0:
            list_process = _("Processus running:\n  - ") + "\n  - ".join(running)
        else:
            list_process = _("No sound process running.")
        return list_process


    def UIlayout(self, layout):
        '''
        layout implementation called in base class to setup UI
        '''
        
        driver = ""
        self.bannerbox = self.factory.createHBox(layout)
        self.banner = self.factory.createImage(self.bannerbox, "/usr/share/icons/sound_section.png")
        vbox = self.factory.createVBox(layout)
        align = self.factory.createLeft(vbox)
        self.factory.createLabel(align,  _("Choose backend for managing sound"), True)
        align = self.factory.createLeft(vbox)
        self.device = self.factory.createLabel(align, self.process_running())
        self.device.setStretchable(1, True)  # 1 : vertical
        # radiobutton to select the backend
        self.backend_rbg = self.factory.createRadioButtonGroup(vbox)
        align = self.factory.createLeft(vbox)
        self.backend_pulse = self.factory.createRadioButton(align, _("Pulseaudio"))
        align = self.factory.createLeft(vbox)
        self.backend_pipe = self.factory.createRadioButton(align, _("Pipewire with Media Session"))
        align = self.factory.createLeft(vbox)
        self.backend_plumb = self.factory.createRadioButton(align, _("Pipewire with Wireplumber"))
        self.backend_rbg.addRadioButton(self.backend_pulse)
        self.backend_rbg.addRadioButton(self.backend_pipe)
        self.backend_rbg.addRadioButton(self.backend_plumb)
        self.backend_pipe.setNotify()
        self.backend_pulse.setNotify()
        self.backend_plumb.setNotify()
        self.eventManager.addWidgetEvent(self.backend_pipe, self.onPipe)
        self.eventManager.addWidgetEvent(self.backend_pulse, self.onPulse)
        self.eventManager.addWidgetEvent(self.backend_plumb, self.onPlumb)
            
        if self.pulse:
            self.backend_pulse.setValue(True)
        if "pipewire-media-session" in self.process_running():
            self.backend_pipe.setValue(True)
        if "wireplumber" in self.process_running():
            self.backend_plumb.setValue(True)
        # buttons on the last line
        align = self.factory.createRight(layout)
        hbox = self.factory.createHBox(align)
        aboutButton = self.factory.createPushButton(hbox, _("&About") )
        self.eventManager.addWidgetEvent(aboutButton, self.onAbout)
        align = self.factory.createRight(hbox)
        hbox     = self.factory.createHBox(align)
        saveButton = self.factory.createPushButton(hbox, _("A&pply"))
        self.eventManager.addWidgetEvent(saveButton, self.onApply)
        quitButton = self.factory.createPushButton(hbox, _("&Quit"))
        self.eventManager.addWidgetEvent(quitButton, self.onQuitEvent)

        # Let's test a cancel event
        self.eventManager.addCancelEvent(self.onQuitEvent)
    
    def is_pulse_installed(self):
      return (os.path.exists("/usr/lib/alsa-lib/libasound_module_pcm_pulse.so")
              or os.path.exists("/usr/lib64/alsa-lib/libasound_module_pcm_pulse.so"))

    def onAbout(self):
      '''
      About menu call back
      '''
      common.AboutDialog({ 'name' : "Test Tabbed About Dialog",
                    'dialog_mode' : common.AboutDialogMode.TABBED,
                    'version' : manatools.__project_version__,
                    'credits' :"Copyright (C) 2023 Angelo Naselli, Papoteur",
                    'license' : 'GPLv2',
                    'authors' : 'Angelo Naselli &lt;anaselli@linux.it&gt;\nPapoteur',
                    'information' : "Created since we have pipewire",
                    'description' : _("This tool allows to select which backend is used for the sound"),
                    'size': {'column': 50, 'lines': 6},
                    })
   
    def onPipe(self):
      '''
      Configure pipewire with media session
      '''
      self.backend_rbg.uncheckOtherButtons(self.backend_pipe)
   
    def onPlumb(self):
      '''
      Configure pipewire with Wireplumber
      '''
      self.backend_rbg.uncheckOtherButtons(self.backend_plumb)

    def onPulse(self):
      '''
      Configure pulseaudio
      '''
      self.backend_rbg.uncheckOtherButtons(self.backend_pulse)

    def onApply(self) :
        '''
        Apply the selected profile
        '''
        yui.YUI.app().busyCursor()
        self._list_services = self.services_object.service_info
        
        if self.backend_rbg.currentButton() == self.backend_pipe:
            self.select_pipewire_mediasession()
        if self.backend_rbg.currentButton() == self.backend_plumb:
            self.select_pipewire_wireplumber()
        if self.backend_rbg.currentButton() == self.backend_pulse:
            self.select_pulseaudio()
        self.device.setLabel(self.process_running())
        yui.YUI.app().redrawScreen()
        yui.YUI.app().normalCursor()


    def systemctl(self, units, command):
        for unit in units:
            if command == "enable":
                subprocess.run(["systemctl", "--user", "--now", command, unit])
            else:
                name, sys_type = unit.split('.')
                if sys_type == "socket":
                    subprocess.run(["systemctl", "--user", "--now", command, unit])
                else:
                    subprocess.run(["systemctl", "--user", "--now", command, unit])
        
    def select_pulseaudio(self):
        if "pipewire" in self._list_services.keys():
            self.systemctl(["pipewire.socket",
                     "pipewire.service",
                     "pipewire-media-session.service",
                     "pipewire-pulse.socket",
                     "pipewire-pulse.service",
                     "wireplumber.service"],
                    "stop"
                     )
            subprocess.run(["systemctl", "--user", "stop", "pipewire.service"])
        self.uninstall(["pipewire-alsa"])
        self.install(["task-pulseaudio", "pulseaudio-module-x11"])
        self.systemctl(["pipewire.service",
                     "pipewire.socket",
                     "pipewire-media-session.service",
                     "pipewire-pulse.service",
                     "wireplumber.service"],
                    "disable"
                     )
        subprocess.run(["/usr/bin/pulseaudio", "--start"])

    def select_pipewire_mediasession(self):
        if "wireplumber" in self._list_services.keys():
            subprocess.run(["systemctl", "--user", "stop", "wireplumber.service"])
            subprocess.run(["systemctl", "--user", "disable", "wireplumber.service"])
        self.install(["task-pipewire", "pipewire-media-session"])
        self.stop_pulseaudio()
        self.systemctl(["pipewire.service", "pipewire-media-session.service",],
                     "enable"
                     )

    def select_pipewire_wireplumber(self):
        self.install(["wireplumber", "task-pipewire"])
        self.stop_pulseaudio()
        self.systemctl(["pipewire-media-session.service",],
                       "disable"
                     )
        self.systemctl(["pipewire.socket",
                     "pipewire.service",
                     "wireplumber.service",
                     "pipewire-pulse.socket"],
                     "enable"
                     )

    def stop_pulseaudio(self):
        proc_iter = psutil.process_iter(attrs=["pid", "name"])
        logging.debug("Looking for pulseaudio process")
        for p in proc_iter:
            if (p.info["name"] == "pulseaudio"):
                logging.debug(f"Found pulseaudio process: {p.info['pid']}")
                psutil.Process(p.info['pid']).kill()

    def onQuitEvent(self) :
        '''
        Quit button call back
        '''
        self.ExitLoop()

if __name__ == '__main__':
    # Send the yui logging outside of the console
    log = yui.YUILog.setLogFileName("/dev/null")
      
    gettext.install('manatools', localedir='/usr/share/locale')
    
    td = SoundDialog()
    td.run()

    common.destroyUI()
  
  
