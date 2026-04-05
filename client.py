import socket
import struct
import threading
import time
import wave
import tkinter as tk
from tkinter import filedialog

from matplotlib.pylab import rint

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5060

# Create UDP socket for SIP communication
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(2)

# Control flags for playback and call state
playing = False
rtp_thread = None
call_active = False
rtcp_thread = None
audio_file = None

# Send INVITE request and process server response
def send_invite():
    global call_active

    invite = """INVITE sip:user@127.0.0.1 SIP/2.0
Via: SIP/2.0/UDP 127.0.0.1:5061
Max-Forwards: 70
Contact: <sip:client1@127.0.0.1>
From: <sip:client1@127.0.0.1>
To: <sip:client2@127.0.0.1>
Call-ID: 1234
CSeq: 1 INVITE
Content-Type: application/sdp
Content-Length: 100

v=0
o=- 0 0 IN IP4 127.0.0.1
s=VoIP Call
c=IN IP4 127.0.0.1
t=0 0
m=audio 5004 RTP/AVP 0
"""
    try:
        # Send INVITE message to server
        sock.sendto(invite.encode(), (SERVER_IP, SERVER_PORT))
        print("INVITE sent")

        # Receive 200 OK response from server
        data, _ = sock.recvfrom(4096)
        response = data.decode()

        # Extract status line (first line)
        status_line = response.split("\n")[0]

        print(f"SIP Response: {status_line}")

        # Check if response is NOT 200 OK
        if not status_line.startswith("SIP/2.0 200"):
            print("❌ SIP Error received. Call failed.")
            call_active = False
            return

        # Parse SDP information from response
        remote_ip = None
        remote_port = None
        codec = None

        for line in response.split("\n"):
            if line.startswith("c="):
                remote_ip = line.split()[-1]

            if line.startswith("m=audio"):
                parts = line.split()
                remote_port = int(parts[1])
                codec = parts[3]

        print(f"Parsed SDP → IP: {remote_ip}, Port: {remote_port}, Codec: {codec}")

        # Send ACK to complete handshake
        ack = "ACK sip:user@127.0.0.1 SIP/2.0\n"
        sock.sendto(ack.encode(), (SERVER_IP, SERVER_PORT))

        call_active = True
        print("ACK sent")

    # Handle failure if server is not available
    except socket.timeout:
        print("❌ Server timeout")
        call_active = False

    except Exception as e:
        print("❌ Error:", e)
        call_active = False


# Send RTP packets with audio data from file
def rtp_stream():
    global playing, call_active

    # Check if file is selected
    if not audio_file:
        print("❌ No audio file selected")
        playing = False
        return

    # Try opening the audio file safely
    try:
        wf = wave.open(audio_file, "rb")
    except Exception as e:
        print("❌ Failed to open audio file:", e)
        playing = False
        return

    sequence = 0
    timestamp = 0
    ssrc = 1234
    chunk_size = 1024


    try:
        while playing and call_active:
            data = wf.readframes(chunk_size)

            # End of file
            if not data:
                print("Audio finished")
                break

            # Build RTP header 
            header = struct.pack(
                "!BBHII",
                (2 << 6),   
                0,          
                sequence,
                timestamp,
                ssrc
            )

            packet = header + data

            try:
                sock.sendto(packet, (SERVER_IP, 5004))
            except Exception as e:
                print("❌ RTP send failed:", e)
                playing = False
                call_active = False
                break

            sequence += 1
            timestamp += chunk_size

            # 48kHz
            time.sleep(chunk_size / 48000)

    except Exception as e:
        print("❌ RTP streaming error:", e)

    finally:
        wf.close()
        playing = False
        print("Streaming stopped")


# Periodically send RTCP packets to server
def rtcp_sender():
    rtcp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send RTCP messages while audio is playing
    while playing and call_active:
        try:
            rtcp_sock.sendto(b"RTCP REPORT", (SERVER_IP, 5005))
            print("RTCP sent")
        except Exception as e:
            print("❌ RTCP failed:", e)
            break

        time.sleep(5)

    rtcp_sock.close()
    print("RTCP stopped")


# Start call and begin RTP and RTCP transmission
def play():
    global playing, rtp_thread, call_active, rtcp_thread

    if playing:
        print("Already playing")
        return

    send_invite()

    # Do not start if call is not established
    if not call_active:
        print("❌ Cannot start playback (no server)")
        return

    playing = True

    # Start RTP streaming thread
    rtp_thread = threading.Thread(target=rtp_stream)
    rtp_thread.start()

    # Start RTCP sending thread
    rtcp_thread = threading.Thread(target=rtcp_sender)
    rtcp_thread.start()

    print("Playback started")


# Pause audio transmission
def pause():
    global playing

    if not playing:
        print("❌ Nothing is playing")
        return

    playing = False
    print("Playback paused")


# Send BYE request and terminate the call
def teardown():
    global playing, call_active

    if not call_active:
        print("❌ No active call")
        return

    playing = False
    call_active = False

    try:
        bye = "BYE sip:user@127.0.0.1 SIP/2.0\n"
        sock.sendto(bye.encode(), (SERVER_IP, SERVER_PORT))
        print("Call terminated")
    except Exception as e:
        print("❌ Failed to send BYE", e)

    # Close SIP socket after call ends
    sock.close()

# Select audio file using file dialog
def select_file():
    global audio_file

    file_path = filedialog.askopenfilename(
        title="Select WAV file",
        filetypes=[("WAV files", "*.wav")]
    )

    if file_path:
        audio_file = file_path
        print(f"Selected file: {audio_file}")

# Create GUI window for controlling the client
root = tk.Tk()
root.title("RTP Client")

frame = tk.Frame(root)
frame.pack(pady=20)

# Button to select audio file
btn_select = tk.Button(frame, text="Select File", width=10, command=select_file)
btn_select.grid(row=0, column=0, padx=5)

# Button to start playback
btn_play = tk.Button(frame, text="Play", width=10, command=play)
btn_play.grid(row=0, column=1, padx=5)

# Button to pause playback
btn_pause = tk.Button(frame, text="Pause", width=10, command=pause)
btn_pause.grid(row=0, column=2, padx=5)

# Button to terminate the call
btn_teardown = tk.Button(frame, text="Teardown", width=10, command=teardown)
btn_teardown.grid(row=0, column=3, padx=5)

# Start GUI event loop
root.mainloop()