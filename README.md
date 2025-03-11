# Real-Time Video Streaming

This repository explores the design and implementation of a real-time video streaming service.

## Architecture

- **Origin Server**: Stores videos and generates UDP packets containing video frames. These packets are only sent when requested by a node.

- **CDN Network**: Consists of multiple distributed nodes responsible for relaying video packets to clients.

- **Points of Presence (POP)**: Act as entry points for clients, connecting them to the CDN network.

- **Clients**: Devices that consume the video streaming content via the CDN.

- **Communication Protocol**: All communication between system components (server, nodes, and clients) occurs over UDP, using an application-layer protocol designed for low-latency video transmission.

This system ensures efficient video distribution, reducing latency and optimizing network traffic.

## Authors

* [João Ferreira](https://github.com/joaohcf)
* [Luís Barros](https://github.com/Luis-Barros9)
* [Luís Borges](https://github.com/bohrges)
