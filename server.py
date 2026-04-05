import socket
import struct
import threading
import pyaudio

HOST = "127.0.0.1"
PORT = 5060

# Control flag for RTP listener loop
running = True


# Receive RTP packets and play audio in real time
def rtp_listener():
    global running

    # Create UDP socket for RTP and bind to port 5004
    rtp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    rtp_sock.bind((HOST, 5004))
    rtp_sock.settimeout(0.5)

    print("RTP listener started on port 5004...")

    # Initialize audio output stream
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=2,
        rate=48000,
        output=True,
        frames_per_buffer=4096
    )

    # Buffer to store incoming audio data before playback
    buffer = b""
    CHUNK = 4096

    # Continuously receive RTP packets while running
    while running:
        try:
            # Receive incoming RTP packet
            packet, addr = rtp_sock.recvfrom(65536)

            # Check if packet contains valid RTP header
            if len(packet) >= 12:
                # Extract RTP payload and header
                payload = packet[12:]
                header = packet[:12]
                fields = struct.unpack("!BBHII", header)

                # Get sequence number and timestamp
                sequence = fields[2]
                timestamp = fields[3]

                print(f"RTP packet received | seq={sequence} | ts={timestamp}")

                # Append payload to buffer
                buffer += payload

                # Play buffered audio in chunks
                while len(buffer) >= CHUNK:
                    stream.write(buffer[:CHUNK])
                    buffer = buffer[CHUNK:]

        # Continue loop if no packet is received within timeout
        except socket.timeout:
            continue

        # Handle unexpected errors
        except Exception as e:
            print("RTP error:", e)
            break

    # Play remaining audio data in buffer
    if buffer:
        stream.write(buffer)

    # Close audio stream and socket
    stream.stop_stream()
    stream.close()
    p.terminate()
    rtp_sock.close()

    print("RTP listener stopped")


# Start RTP listener in a separate thread
rtp_thread = threading.Thread(target=rtp_listener, daemon=True)
rtp_thread.start()


# Create UDP socket for SIP signaling
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("SIP Server running... waiting for INVITE")


# Receive and process SIP messages
while True:
    data, addr = sock.recvfrom(4096)
    message = data.decode(errors="ignore")

    print("\nReceived:")
    print(message)

    # Handle INVITE request and send 200 OK response
    if "INVITE" in message:
        print("INVITE received, sending 200 OK")

        response = """SIP/2.0 200 OK
        Via: SIP/2.0/UDP 127.0.0.1:5060
        From: <sip:client1@127.0.0.1>
        To: <sip:client2@127.0.0.1>
        Call-ID: 1234
        CSeq: 1 INVITE
        Content-Length: 0

        """

        # for error testing
        #print("Sending 404 Not Found")

        #response = """SIP/2.0 404 Not Found
        #Via: SIP/2.0/UDP 127.0.0.1:5060
        #From: <sip:client1@127.0.0.1>
        #To: <sip:client2@127.0.0.1>
        #Call-ID: 1234
        #CSeq: 1 INVITE
        #Content-Length: 0
        #"""
        sock.sendto(response.encode(), addr)

    # Handle ACK request to confirm call establishment
    elif "ACK" in message:
        print("ACK received. Call established!")

    # Handle BYE request to terminate the call
    elif "BYE" in message:
        print("BYE received. Closing call.")
        running = False
        break


# Close SIP socket after call termination
sock.close()
print("Server shutdown complete")