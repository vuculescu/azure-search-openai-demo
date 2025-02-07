import logging

from openai import APIError
from quart import jsonify

ERROR_MESSAGE = """The app encountered an error processing your request.
If you are an administrator of the app, view the full error in the logs. See aka.ms/appservice-logs for more information.
Error type: {error_type}
"""
ERROR_MESSAGE_FILTER = """Your message contains content that was flagged by the OpenAI content filter."""

ERROR_MESSAGE_LENGTH = """Your message exceeded the context length limit for this OpenAI model. Please shorten your message or change your settings to retrieve fewer search results."""

ERROR_MESSAGE_RATE_LIMIT = """Sorry, you have reached the weekly question limit. You have already asked {count} questions! We appreciate your enthusiasm, but to keep things fair, you cannot ask Phil any more questions until your quota gets reset. Your quota gets reset automatically every week. Please try again in a few days."""

def error_dict(error: Exception) -> dict:
    if isinstance(error, APIError) and error.code == "content_filter":
        return {"error": ERROR_MESSAGE_FILTER}
    if isinstance(error, APIError) and error.code == "context_length_exceeded":
        return {"error": ERROR_MESSAGE_LENGTH}
    if "Rate limit exceeded:" in str(error):
        count = int(str(error).split("/")[0].split(":")[-1].strip())
        return {"error": ERROR_MESSAGE_RATE_LIMIT.format(count=count)}
    return {"error": ERROR_MESSAGE.format(error_type=type(error))}

def error_response(error: Exception, route: str, status_code: int = 500):
    logging.exception("Exception in %s: %s", route, error)
    if isinstance(error, APIError) and error.code == "content_filter":
        status_code = 400
    return jsonify(error_dict(error)), status_code
