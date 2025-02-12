import json
from typing import Any

class Message:
    """
    Representasi pesan dalam sistem.
    Pesan memiliki tipe dan data, dan dapat diserialisasi ke format JSON.
    """
    def __init__(self, msg_type: str, data: Any) -> None:
        """
        Inisialisasi pesan dengan tipe dan data.
        
        Args:
            msg_type (str): Jenis pesan.
            data (Any): Isi data pesan yang harus serializable ke JSON.
        """
        self._msg_type = msg_type
        self._data = data

    @property
    def msg_type(self) -> str:
        """Mengembalikan tipe pesan."""
        return self._msg_type

    @property
    def data(self) -> Any:
        """Mengembalikan data pesan."""
        return self._data

    def to_json(self) -> str:
        """
        Menyerialisasi pesan menjadi string JSON.
        
        Returns:
            str: Representasi JSON dari pesan.
        """
        return json.dumps({"type": self._msg_type, "data": self._data})

    @staticmethod
    def from_json(json_str: str) -> "Message":
        """
        Membuat objek Message dari string JSON.
        
        Args:
            json_str (str): String JSON yang berisi pesan.
        
        Returns:
            Message: Objek Message yang dihasilkan.
        
        Raises:
            ValueError: Jika format JSON tidak valid atau kunci yang diperlukan tidak ditemukan.
        """
        try:
            data = json.loads(json_str)
            msg_type = data["type"]
            msg_data = data["data"]
        except (KeyError, json.JSONDecodeError) as e:
            raise ValueError("Invalid JSON message format") from e
        return Message(msg_type, msg_data)

    def __repr__(self) -> str:
        return f"Message(type={self._msg_type!r}, data={self._data!r})"

    def __str__(self) -> str:
        return self.to_json()
