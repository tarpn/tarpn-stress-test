import argparse
import asyncio
from functools import partial
import logging
import time

import telnetlib3
from telnetlib3.stream_reader import TelnetReader
from telnetlib3.stream_writer import TelnetWriter


async def read_until(reader, s):
    buf = ""
    while True:
        try:
            buf += await asyncio.wait_for(reader.read(1), timeout=30.0)
            if buf.endswith(s):
                return buf
        except asyncio.TimeoutError:
            raise RuntimeError(f"Never found {s} in the output \"{buf}\". Aborting")


async def empty_reader(reader, timeout=10):
    await asyncio.shield(asyncio.wait_for(reader.read(1024), timeout=timeout))


async def neighbor_shell(
    username: str,
    our_node: str,
    neighbor: str,
    reader: TelnetReader,
    writer: TelnetWriter
):
    logger = logging.getLogger(neighbor)

    user_sent = False
    pwd_sent = False
    connected = False
    finished_reading = False

    logger.info(f"Testing via {neighbor}")
    file_size_times_2 = 20000
    line_buffer = ""
    while True:
        line = await reader.read(32)
        #logger.info(line)
        line_buffer += line
        line_buffer = line_buffer[-100:]
        if not user_sent:
            if line.endswith(":"):
                writer.write(f"{username}\r\n")
                user_sent = True
        elif not pwd_sent:
            if line.endswith(":"):
                writer.write("p\r\n")
                pwd_sent = True
        elif not connected:
            await empty_reader(reader)
            logger.info(f"Connecting to {neighbor}")
            writer.write(f"C {neighbor}\r\n")
            await read_until(reader, "Connected")
            await empty_reader(reader)
            logger.info("Connected! Now connecting back to your node...")
            writer.write(f"C {our_node}\r\n")
            await read_until(reader, "Connected")
            logger.info("Loop established.  Starting stress test.")
            await empty_reader(reader)
            #logger.info("Listing files..")
            writer.write("BBS\r\n")
            await read_until(reader, "Boss")
            #try:
                # File size is 2x since we are reading it from ourselves through our neighbor
            #    logger.info(f"Found g8bpqloop.txt! Now reading it.")
            #except:
            #    logger.info("Could not find g8bpqloop.txt, aborting.")
            #    writer.write("BYE\r\n")
            #    break
            writer.write("read g8bpqloop.txt\r\n")
            start = time.time()
            connected = True
        elif not finished_reading:
            if "End of File" in line_buffer:
                finished_reading = True
                end = time.time()
            elif "Invalid command" in line_buffer:
                logger.info("Aborting")
                end = time.time()
                break
        else:
           # logger.info("Leaving")
            await asyncio.sleep(5)
            writer.write("BYE\r\n")
            await asyncio.sleep(5)
            writer.write("BYE\r\n")
            break

    try:
        dt = end - start
        rate = file_size_times_2 / dt
        logger.info(f"10K bytes in {dt:0.2f} seconds at a rate of {rate:0.2f} bytes/sec.")
    except:
        logger.error("Something went wrong.")


async def connect_to_neighbor(username, hostname, node, neighbor):
    factory = partial(neighbor_shell, username, node, neighbor)
    reader, writer = await telnetlib3.open_connection(hostname, 8010, shell=factory)
    await writer.protocol.waiter_closed


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s -- %(message)s')
    parser = argparse.ArgumentParser(description='Connect to neighbors and read their g8bpqloop.txt file')
    parser.add_argument("callsign", help="Your call sign, without any \"-2\" part. E.g., \"k4dbz\"")
    parser.add_argument("tarpn_hostname", help="IP address of your TARPN node")
    parser.add_argument("node", help="Your node callsign with the \"-2\" part. E.g., \"K4DBZ-2\"")
    parser.add_argument("neighbors", help="Comma-separated list of neighbor callsigns. E.g., \"KA2DEW-2, KN4ORB-2\"")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    tasks = []
    for neighbor in args.neighbors.split(","):
        neighbor = neighbor.strip()
        logging.info(f"Scheduling task for {neighbor}")
        tasks.append(connect_to_neighbor(args.callsign, args.tarpn_hostname, args.node, neighbor))
    all_tasks = asyncio.gather(*tasks)
    loop.run_until_complete(all_tasks)


if __name__ == "__main__":
    main()
