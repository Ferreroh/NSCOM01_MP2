Ferrer, Angel June E.
Coluso, Zen Matthew R.

NSCOM01 – Machine Project #2
Real-Time Audio Streaming over IP

Term 2, AY 2025–2026
1. Introduction

    This project implements a simple Voice over IP (VoIP) system using UDP sockets. Since UDP does not guarantee delivery, ordering, or session control, this implementation separates communication into various protocols to simulate real-world VoIP systems.

    The system is inspired by standard VoIP protocols such as:
        - SIP (Session Initiation Protocol) for signaling
        - RTP (Real-time Transport Protocol) for audio streaming
        - RTCP (RTP Control Protocol) for monitoring

    The system supports:
        - One-way audio streaming (Client → Server)
        - Real-time playback of .wav audio files
        - Basic call control (select file, play, pause, teardown)

    All communication is performed over UDP sockets.

2. Protocol Overview

    The system is divided into three main components:
        - SIP (Signaling) → Call setup and teardown
        - RTP (Media Transport) → Audio streaming
        - RTCP (Control) → Monitoring

    2.1 Session Establishment (SIP Handshake)
        2.1.1 Client sends INVITE
        2.1.2 Server replies with 200 OK
        2.1.3 Client sends ACK
        2.1.4 Call session is established

        The INVITE message includes:
            - IP address
            - Audio port
            - Codec type

    2.2 Audio Streaming (RTP)
        2.2.1 Client reads audio from a .wav file
        2.2.2 Audio is split into chunks
        2.2.3 Each chunk is encapsulated in an RTP packet
        2.2.4 RTP packets are sent over UDP (port 5004)
        2.2.5 Server:
            - Extracts RTP header
            - Buffers payload
            - Plays audio in real time

    2.3 RTCP Monitoring
        2.3.1 Client sends RTCP packets periodically
        2.3.2 Messages are sent every 5 seconds
        2.3.3 Used for:
            - Connection monitoring
            - Stream status reporting

    2.4 Call Termination
        2.4.1 Client sends BYE
        2.4.2 Server stops RTP listener
        2.4.3 Session is terminated cleanly

    2.5 Protocol Message Flow Diagram

        Client                          Server
        |------ INVITE ----------------->|
        |<----- 200 OK ------------------|
        |------ ACK -------------------->|
        |========= AUDIO STREAM =========|
        |------ RTP packets ----------->|
        |------ RTCP reports ---------->|
        |------ BYE -------------------->|

3. Packet Message Format

    3.1 SIP Messages
        Text-based protocol containing:
            - Method (INVITE, ACK, BYE)
            - Headers (Via, From, To, Call-ID)
            - Optional SDP body

    3.2 RTP Packet Structure (12-byte header)
        Field                  Size        Description
        Version/Padding       1 byte       RTP version info
        Payload Type          1 byte       Codec identifier
        Sequence Number       2 bytes      Packet order
        Timestamp             4 bytes      Playback timing
        SSRC                  4 bytes      Stream identifier

        Payload:
            - Raw audio data from .wav file

    3.3 RTCP Messages
        Simple control messages:
            - Sent as plain text: "RTCP REPORT"
            - Used for monitoring only

4. State Machines

    4.1 Client State Machine

        IDLE
        → SEND_INVITE
        → WAIT_RESPONSE
        → SEND_ACK
        → STREAMING
        → SEND_BYE
        → CLOSED

    4.2 Server State Machine

        LISTEN
        → RECEIVE_INVITE
        → SEND_200_OK
        → WAIT_ACK
        → RECEIVE_RTP
        → RECEIVE_BYE
        → CLOSED

5. Reliability Mechanisms

    Since UDP is unreliable, this implementation uses simplified mechanisms:

    5.1 Real-Time Streaming
        - Continuous RTP packet transmission
        - No retransmission (prioritizes real-time playback)

    5.2 Sequence Numbers
        - Each RTP packet includes a sequence number
        - Used for tracking order

    5.3 Buffering
        - Server buffers incoming audio before playback
        - Ensures smoother playback

    5.4 Timing Control
        - Client uses sleep intervals to simulate real-time streaming

6. Error Handling

    The system handles errors gracefully without crashing:

    6.1 SIP Errors (4xx, 5xx)
        - Client checks SIP response status
        - If not 200 OK:
            - Logs error
            - Aborts call setup

    6.2 Timeout
        - If no response is received:
            - Client detects timeout
            - Call setup fails safely

    6.3 RTP Errors
        - If packet sending fails:
            - Streaming stops
            - Error is logged

    6.4 Invalid or Unexpected Packets
        - Server ignores malformed RTP packets
        - Exceptions are caught and logged

    6.5 File Errors
        - If no .wav file is selected:
            - Playback does not start
        - If file cannot be opened:
            - Error is printed
            - Streaming stops safely

7. Audio Streaming Operation

    Client:
        - Selects a .wav file via GUI
        - Reads file in binary mode
        - Sends audio as RTP packets

    Server:
        - Receives RTP packets
        - Extracts payload
        - Plays audio using PyAudio

8. End-of-Stream Handling

    End of audio is detected when:
        - No more frames are read from the .wav file

    Client:
        - Stops sending RTP packets

    Server:
        - Plays remaining buffered audio
        - Stops playback

9. How to Run

    Install dependencies:
        pip install pyaudio

    Start server:
        python3 server.py

    Start client:
        python3 client.py

    Usage:
        1. Click "Select File" and choose a .wav file
        2. Click "Play" to start streaming
        3. Click "Pause" to stop temporarily
        4. Click "Teardown" to end the call

10. Test Cases

    10.1 Normal Streaming
        Output (Client Side):
        INVITE sent
        SIP Response: SIP/2.0 200 OK
        Parsed SDP → IP: None, Port: None, Codec: None
        ACK sent
        Playback started
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        RTCP sent
        Audio finished
        Streaming stopped
        RTCP stopped

        Output (Server Side):
        RTP listener started on port 5004...
        SIP Server running... waiting for INVITE

        Received:
        INVITE sip:user@127.0.0.1 SIP/2.0
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

        INVITE received, sending 200 OK

        Received:
        ACK sip:user@127.0.0.1 SIP/2.0

        ACK received. Call established!
        RTP packet received | seq=0 | ts=0
        RTP packet received | seq=1 | ts=1024
        RTP packet received | seq=2 | ts=2048
        RTP packet received | seq=3 | ts=3072
        RTP packet received | seq=4 | ts=4096
        RTP packet received | seq=5 | ts=5120 (ETC.)

    10.2 Receiving Garbage Packet ("RANDOM" string)
        Output (Client Side):
        INVITE sent
        SIP Response: RANDOM
        ❌ SIP Error received. Call failed.
        ❌ Cannot start playback (no server)

    10.3 Timeout
        Output (Client Side):
        INVITE sent
        ❌ Server not available
        ❌ Cannot start playback (no server)