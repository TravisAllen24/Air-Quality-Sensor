import board # type: ignore
import storage # type: ignore
import sdcardio # type: ignore

class SDCardManager:

    def __init__(self):
        # Set up SPI and SD card
        spi = board.SPI()
        cs_pin=board.D10
        self.sdcard = sdcardio.SDCard(spi, cs_pin)
        # Mount SD card
        vfs = storage.VfsFat(self.sdcard)
        storage.mount(vfs, "/sd")

        self.mount()


    def mount(self):
        """Mount the SD card."""
        vfs = storage.VfsFat(self.sdcard)
        storage.mount(vfs, "/sd")

    def unmount(self):
        """Unmount the SD card safely."""
        storage.umount("/sd")