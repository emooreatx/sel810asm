import struct
import sys

START_CODE = 0xff
CARRIAGE_RETURN = 0x8d
LINE_FEED = 0x8a

class RS227():
	def __init__(self,file, feeder_code=b"\x00", trailer_code=b"\xff"):
		self.filename = file
		
		self.fp = None
		self.feeder_code = feeder_code
		self.trailer_code = trailer_code
		
	def _read_tape_leader(self):
		a = 0x00
		while a != CARRIAGE_RETURN:
			a = ord(self.fp.read(1))
		a = ord(self.fp.read(1))
		if a != LINE_FEED:
			raise ValueError
			
	def _read_tape_code(self):
		return ord(self.fp.read(1))

	def _read_tape_frame(self):
		rawbytes = self.fp.read(108)
		rawframe = struct.unpack("108B",rawbytes)
		frame = [rawframe[i] << 16 | rawframe[i + 1] << 8 | rawframe[i + 2] for i in range(0, len(rawframe), 3)]
		check = struct.unpack(">h",self.fp.read(2))[0]
		crlf = struct.unpack("BB",self.fp.read(2))
		check2 = self._crc(struct.unpack(">54H",rawbytes))
		return (check,check2,frame)

	def read_contents(self, ignore_errors=False):
		self.fp = open(self.filename,"rb")
		self._read_tape_leader()
		tc = self._read_tape_code()
		full_tape = []
		while tc == START_CODE:
			(check, check2, frame) = self._read_tape_frame()
			if ignore_errors != True:
				if check != check2:
					raise ValueError
			full_tape = full_tape + frame
			tc = self._read_tape_code()
		self.close()
		return full_tape

	def _crc(self,contents): # takes a list of shorts
		check = 0x0000
		for i in contents:
			check = (check + i)  & 0xffff
		return struct.unpack(">h",struct.pack(">H",check))[0] * -1

	def write_contents(self, contents,  leader_len=20, trailer_len=20):
		self.fp = open(self.filename,"wb")

		#fixme
		for i in range(leader_len):
			self.fp.write(self.feeder_code)

		self.fp.write(b"\x8d\x8a");
		for i in range(0,len(contents),108):
			self.fp.write(b"\xff");
			chunk =contents[i:i+108]
			while len(chunk) < 108:
				chunk += b'\x00'
			self.fp.write(chunk)
			crc = self._crc(struct.unpack(">%dH" % (len(chunk)/2),chunk))
			self.fp.write(struct.pack(">h",crc))
			self.fp.write(b"\x8d\x8a");
		self.fp.write(b"\x00");

		for i in range(trailer_len):
			self.fp.write(self.trailer_code)

		self.close()
		
	def close(self):
		self.fp.close()


if __name__ == '__main__':
	tape = RS227(sys.argv[1])
	(tape.read_contents())
