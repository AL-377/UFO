# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import abc
from importlib import import_module

class BaseService(abc.ABC):
    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def chat_completion(self, *args, **kwargs):
        pass

    @staticmethod
    def get_service(name,model_name=None):
        service_map = {
            "openai": "OpenAIService",
            "aoai": "OpenAIService",
            "azure_ad": "OpenAIService",
            "qwen": "QwenService",
            "ollama": "OllamaService",
            "gemini": "GeminiService",
            "placeholder": "PlaceHolderService",
            "lam":"LAMService",
        }
        custom_service_map = {
            'llava': 'LlavaService'
        }
        service_name = service_map.get(name, None)
        if service_name:
            if name in ['aoai', 'azure_ad']:
                module = import_module('.openai', package='ufo.llm')
            elif service_name == 'CustomService':
                custom_model = 'llava' if 'llava' in model_name else model_name
                custom_service_name = custom_service_map.get('llava' if 'llava' in custom_model else custom_model, None)
                if custom_service_name:
                    module = import_module('.'+custom_model, package='ufo.llm')
                    service_name = custom_service_name
                else:
                    raise ValueError(f'Custom model {custom_model} not supported')
            else:
                module = import_module('.'+name.lower(), package='ufo.llm')
            return getattr(module, service_name)
        else:
            raise ValueError(f"Service {name} not found.")

    def get_cost_estimator(
        self, api_type, model, prices, prompt_tokens, completion_tokens
    ) -> float:
        """
        Calculates the cost estimate for using a specific model based on the number of prompt tokens and completion tokens.

        Args:
            model (str): The name of the model.
            prices (dict): A dictionary containing the prices for different models.
            prompt_tokens (int): The number of prompt tokens used.
            completion_tokens (int): The number of completion tokens used.

        Returns:
            float: The estimated cost for using the model.
        """
        if api_type.lower() == "openai":
            name = str(api_type + "/" + model)
        elif api_type.lower() in ["aoai", "azure_ad"]:
            name = str("azure/" + model)
        elif api_type.lower() == "qwen":
            name = str("qwen/" + model)
        elif api_type.lower() == "gemini":
            name = str("gemini/" + model)

        if name in prices:
            cost = (
                prompt_tokens * prices[name]["input"] / 1000
                + completion_tokens * prices[name]["output"] / 1000
            )
        else:
            return 0
        return cost
