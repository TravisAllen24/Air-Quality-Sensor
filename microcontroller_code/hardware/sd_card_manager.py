import storage # type: ignore
import sdcardio # type: ignore

class SDCardManager:

    def __init__(self, spi, cs_pin):
        # Set up SD card
        self.sdcard = sdcardio.SDCard(spi, cs_pin)

        # Mount SD card
        self.mount_path = "/sd"
        self.mount()

    def mount(self):
        """Mount the SD card."""
        vfs = storage.VfsFat(self.sdcard)
        storage.mount(vfs, self.mount_path)

    def unmount(self):
        """Unmount the SD card safely."""
        storage.umount(self.mount_path)
        