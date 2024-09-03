"""OpenAI API Compatible generators

Supports chat + chatcompletion models. Put your API key in
an environment variable documented in the selected generator. Put the name of the
model you want in either the --model_name command line parameter, or
pass it as an argument to the Generator constructor.

sources:
* https://platform.openai.com/docs/models/model-endpoint-compatibility
* https://platform.openai.com/docs/model-index-for-researchers
"""

import json
import logging
import re
from typing import List, Union

import openai
import backoff

from garak import _config
import garak.exception
from garak.generators.base import Generator

# lists derived from https://platform.openai.com/docs/models
chat_models = (
    "gpt-4",  # links to latest version
    "gpt-4-turbo",  # links to latest version
    "gpt-4o",  # links to latest version
    "gpt-4o-mini",  # links to latest version
    "gpt-4-turbo-preview",
    "gpt-3.5-turbo",  # links to latest version
    "gpt-4-32k",
    "gpt-4-0125-preview",
    "gpt-4-1106-preview",
    "gpt-4-vision-preview",
    "gpt-4-1106-vision-preview",
    "gpt-4-0613",
    "gpt-4-32k",
    "gpt-4-32k-0613",
    "gpt-3.5-turbo-0125",
    "gpt-3.5-turbo-1106",
    "gpt-3.5-turbo-16k",
    "gpt-3.5-turbo-0613",  # deprecated, shutdown 2024-06-13
    "gpt-3.5-turbo-16k-0613",  # # deprecated, shutdown 2024-06-13
)

completion_models = (
    "gpt-3.5-turbo-instruct",
    "davinci-002",
    "babbage-002",
    "davinci-instruct-beta",  # unknown status
    # "text-davinci-003", # shutdown https://platform.openai.com/docs/deprecations
    # "text-davinci-002", # shutdown https://platform.openai.com/docs/deprecations
    # "text-curie-001", # shutdown https://platform.openai.com/docs/deprecations
    # "text-babbage-001", # shutdown https://platform.openai.com/docs/deprecations
    # "text-ada-001", # shutdown https://platform.openai.com/docs/deprecations
    # "code-davinci-002", # shutdown https://platform.openai.com/docs/deprecations
    # "code-davinci-001", # shutdown https://platform.openai.com/docs/deprecations
    # "davinci",  # shutdown https://platform.openai.com/docs/deprecations
    # "curie",  # shutdown https://platform.openai.com/docs/deprecations
    # "babbage",  # shutdown https://platform.openai.com/docs/deprecations
    # "ada",  # shutdown https://platform.openai.com/docs/deprecations
)

context_lengths = {
    "gpt-3.5-turbo-0125": 16385,
    "gpt-3.5-turbo": 16385,
    "gpt-3.5-turbo-1106": 16385,
    "gpt-3.5-turbo-instruct": 4096,
    "gpt-3.5-turbo-16k": 16385,
    "gpt-3.5-turbo-0613": 4096,
    "gpt-3.5-turbo-16k-0613": 16385,
    "babbage-002": 16384,
    "davinci-002": 16384,
    "gpt-4-turbo": 128000,
    "gpt-4-turbo-2024-04-09": 128000,
    "gpt-4-turbo-preview": 128000,
    "gpt-4-0125-preview": 128000,
    "gpt-4-1106-preview": 128000,
    "gpt-4-vision-preview": 128000,
    "gpt-4-1106-vision-preview": 128000,
    "gpt-4": 8192,
    "gpt-4-0613": 8192,
    "gpt-4-32k": 32768,
    "gpt-4-32k-0613": 32768,
}


class OpenAICompatible(Generator):
    """Generator base class for OpenAI compatible text2text restful API. Implements shared initialization and execution methods."""

    ENV_VAR = "OpenAICompatible_API_KEY".upper()  # Placeholder override when extending

    active = False  # this interface class is not active
    supports_multiple_generations = True
    generator_family_name = "OpenAICompatible"  # Placeholder override when extending

    # template defaults optionally override when extending
    DEFAULT_PARAMS = Generator.DEFAULT_PARAMS | {
        "temperature": 0.7,
        "top_p": 1.0,
        "frequency_penalty": 0.0,
        "presence_penalty": 0.0,
        "seed": None,
        "stop": ["#", ";"],
        "suppressed_params": set(),
        "retry_json": True,
    }

    # avoid attempt to pickle the client attribute
    def __getstate__(self) -> object:
        self._clear_client()
        return dict(self.__dict__)

    # restore the client attribute
    def __setstate__(self, d) -> object:
        self.__dict__.update(d)
        self._load_client()

    def _load_client(self):
        # Required stub implemented when extending `OpenAICompatible`
        # should populate self.generator with an openai api compliant object
        raise NotImplementedError

    def _clear_client(self):
        # Required stub implemented when extending `OpenAICompatible`
        raise NotImplementedError

    def _validate_config(self):
        pass

    def __init__(self, name="", config_root=_config):
        self.name = name
        self._load_config(config_root)
        self.fullname = f"{self.generator_family_name} {self.name}"
        self.key_env_var = self.ENV_VAR

        self._load_client()

        if self.generator not in (
            self.client.chat.completions,
            self.client.completions,
        ):
            raise ValueError(
                "Unsupported model at generation time in generators/openai.py - please add a clause!"
            )

        self._validate_config()

        super().__init__(self.name, config_root=config_root)

        # clear client config to enable object to `pickle`
        self._clear_client()

    # noinspection PyArgumentList
    @backoff.on_exception(
        backoff.fibo,
        (
            openai.RateLimitError,
            openai.InternalServerError,
            openai.APITimeoutError,
            openai.APIConnectionError,
            garak.exception.GarakBackoffTrigger,
        ),
        max_value=70,
    )
    def _call_model(
        self, prompt: Union[str, List[dict]], generations_this_call: int = 1
    ) -> List[Union[str, None]]:
        if self.client is None:
            # reload client once when consuming the generator
            self._load_client()

        create_args = {
            "model": self.name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "n": generations_this_call,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "stop": self.stop,
            "seed": self.seed,
        }

        create_args = {
            k: v
            for k, v in create_args.items()
            if v is not None and k not in self.suppressed_params
        }

        if self.generator == self.client.completions:
            if not isinstance(prompt, str):
                msg = (
                    f"Expected a string for {self.generator_family_name} completions model {self.name}, but got {type(prompt)}. "
                    f"Returning nothing!"
                )
                logging.error(msg)
                return list()

            create_args["prompt"] = prompt

        elif self.generator == self.client.chat.completions:
            if isinstance(prompt, str):
                messages = [{"role": "user", "content": prompt}]
            elif isinstance(prompt, list):
                messages = prompt
            else:
                msg = (
                    f"Expected a list of dicts for {self.generator_family_name} Chat model {self.name}, but got {type(prompt)} instead. "
                    f"Returning nothing!"
                )
                logging.error(msg)
                return list()

            create_args["messages"] = messages

        try:
            response = self.generator.create(**create_args)
        except openai.BadRequestError as e:
            msg = "Bad request: " + str(repr(prompt))
            logging.exception(e)
            logging.error(msg)
            return [None]
        except json.decoder.JSONDecodeError as e:
            logging.exception(e)
            if self.retry_json:
                raise garak.exception.GarakBackoffTrigger from e
            else:
                raise e

        if self.generator == self.client.completions:
            return [c.text for c in response.choices]
        elif self.generator == self.client.chat.completions:
            return [c.message.content for c in response.choices]


class OpenAIGenerator(OpenAICompatible):
    """Generator wrapper for OpenAI text2text models. Expects API key in the OPENAI_API_KEY environment variable"""

    ENV_VAR = "OPENAI_API_KEY"
    active = True
    generator_family_name = "OpenAI"

    def _load_client(self):
        self.client = openai.OpenAI(api_key=self.api_key)

        if self.name == "":
            openai_model_list = sorted([m.id for m in self.client.models.list().data])
            raise ValueError(
                f"Model name is required for {self.generator_family_name}, use --model_name\n"
                + "  API returns following available models: ▶️   "
                + "  ".join(openai_model_list)
                + "\n"
                + "  ⚠️  Not all these are text generation models"
            )

        if self.name in completion_models:
            self.generator = self.client.completions
        elif self.name in chat_models:
            self.generator = self.client.chat.completions
        elif "-".join(self.name.split("-")[:-1]) in chat_models and re.match(
            r"^.+-[01][0-9][0-3][0-9]$", self.name
        ):  # handle model names -MMDDish suffix
            self.generator = self.client.completions
        else:
            raise ValueError(
                f"No {self.generator_family_name} API defined for '{self.name}' in generators/openai.py - please add one!"
            )

    def _clear_client(self):
        self.generator = None
        self.client = None

    def __init__(self, name="", config_root=_config):
        self.name = name
        self._load_config(config_root)
        if self.name in context_lengths:
            self.context_len = context_lengths[self.name]

        super().__init__(self.name, config_root=config_root)


DEFAULT_CLASS = "OpenAIGenerator"
