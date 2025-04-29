"""
=============================================================================

 Licensed Materials, Property of Ralph Vogl, Munich

 Project : basefunctions

 Copyright (c) by neuraldevelopment

 All rights reserved.

 Description:

 Generic ThreadPool downloader that loads data from a URL and returns
 JSON, text or binary content depending on Content-Type header.

=============================================================================
"""

# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------
import requests
import basefunctions

# -------------------------------------------------------------
# DEFINITIONS REGISTRY
# -------------------------------------------------------------

# -------------------------------------------------------------
# DEFINITIONS
# -------------------------------------------------------------

# -------------------------------------------------------------
# VARIABLE DEFINITIONS
# -------------------------------------------------------------


# -------------------------------------------------------------
# CLASS / FUNCTION DEFINITIONS
# -------------------------------------------------------------
@basefunctions.task_handler("URLDOWNLOADER")
def url_downloader(thread_local_data, input_queue, message):
    """
    Download the content of a URL provided in message.content.

    The result type is chosen based on the HTTP Content-Type header.

    Parameters
    ----------
    thread_local_data : Any
        Thread-local context (unused).
    input_queue : queue.Queue
        Input queue (unused).
    message : basefunctions.ThreadPoolMessage
        Message containing URL.

    Returns
    -------
    Tuple[bool, Any]
        (success flag, content or error string)
    """
    try:
        response = requests.get(message.content, timeout=message.timeout)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()

        if "application/json" in content_type:
            return True, response.json()
        elif "text/" in content_type or "application/xml" in content_type:
            return True, response.text
        else:
            return True, response.content

    except requests.exceptions.Timeout as e:
        return False, f"Timeout: {e}"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP error: {e.response.status_code} - {e.response.reason}"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {e}"
    except Exception as e:
        return False, f"Unexpected error: {type(e).__name__}: {e}"
