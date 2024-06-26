# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
import heapq
import re
import warnings
from abc import abstractmethod
from typing import Dict, List

warnings.filterwarnings("ignore")


class ControlFilterFactory:
    """
    Factory class to filter control items.
    """

    @staticmethod
    def create_control_filter(control_filter_type: str, *args, **kwargs):
        """
        Create a control filter model based on the given type.
        :param control_filter_type: The type of control filter model to create.
        :return: The created retriever.
        """
        if control_filter_type == "text":
            return TextControlFilter(*args, **kwargs)
        elif control_filter_type == "semantic":
            return SemanticControlFilter(*args, **kwargs)
        elif control_filter_type == "icon":
            return IconControlFilter(*args, **kwargs)
        else:
            raise ValueError("Invalid retriever type: {}".format(control_filter_type))

    @staticmethod
    def inplace_append_filtered_annotation_dict(
        filtered_control_dict: Dict, control_dicts: Dict
    ):
        
        # 
        """
        Appends the given control_info to the filtered_control_dict if it is not already present.
        For example, if the filtered_control_dict is empty, it will be updated with the control_info. The operation is performed in place.

        Args:
            filtered_control_dict (dict): The dictionary of filtered control information.
            control_dicts (dict): The control information to be appended.

        Returns:
            dict: The updated filtered_control_dict dictionary.
        """
        if control_dicts:
            filtered_control_dict.update(
                {
                    k: v
                    for k, v in control_dicts.items()
                    if k not in filtered_control_dict
                }
            )
        return filtered_control_dict

    @staticmethod
    def get_plans(plan: List[str], topk_plan: int) -> List[str]:
        """
        Parses the given plan and returns a list of plans up to the specified topk_plan.

        Args:
            plan (str): The plan to be parsed.
            topk_plan (int): The maximum number of plans to be returned.

        Returns:
            list: A list of plans up to the specified topk_plan.
        """
        return plan[:topk_plan]


class BasicControlFilter:
    """
    BasicControlFilter represents a model for filtering control items.
    """

    _instances = {}

    def __new__(cls, model_path):
        """
        Creates a new instance of BasicControlFilter.
        Args:
            model_path (str): The path to the model.
        Returns:
            BasicControlFilter: The BasicControlFilter instance.
        """
        if model_path not in cls._instances:
            instance = super(BasicControlFilter, cls).__new__(cls)
            instance.model = cls.load_model(model_path)
            cls._instances[model_path] = instance
        return cls._instances[model_path]

    @staticmethod
    def load_model(model_path):
        """
        Loads the model from the given model path.
        Args:
            model_path (str): The path to the model.
        Returns:
            SentenceTransformer: The loaded SentenceTransformer model.
        """
        import sentence_transformers

        return sentence_transformers.SentenceTransformer(model_path)

    def get_embedding(self, content):
        """
        Encodes the given object into an embedding.
        Args:
            content: The content to encode.
        Returns:
            The embedding of the object.
        """
        return self.model.encode(content)

    @abstractmethod
    def control_filter(self, control_dicts, plans, **kwargs):
        """
        Calculates the cosine similarity between the embeddings of the given keywords and the control item.
        Args:
            control_dicts (dic): The control item to be compared with the plans.
            plans (str): The plans to be used for calculating the similarity.
        Returns:
            float: The cosine similarity between the embeddings of the keywords and the control item.
        """
        pass

    @staticmethod
    def plans_to_keywords(plans: List[str]) -> List[str]:
        """
        Gets keywords from the plan.
        We only consider the words in the plan that are alphabetic or Chinese characters.
        Args:
            plans (list): The plan to be parsed.
        Returns:
            list: A list of keywords extracted from the plan.
        """

        keywords = []
        for plan in plans:
            words = plan.replace("'", "").strip(".").split()
            words = [
                word
                for word in words
                if word.isalpha() or bool(re.fullmatch(r"[\u4e00-\u9fa5]+", word))
            ]
            keywords.extend(words)
        return keywords

    @staticmethod
    def remove_stopwords(keywords):
        """
        Removes stopwords from the given list of keywords.
        Note:
            If you are using stopwords for the first time, you need to download them using nltk.download('stopwords').
        Args:
            keywords (list): A list of keywords.
        Returns:
            list: A list of keywords with the stopwords removed.
        """

        try:
            from nltk.corpus import stopwords

            stopwords_list = stopwords.words("english")
        except LookupError as e:
            import nltk

            nltk.download("stopwords")
            stopwords_list = nltk.corpus.stopwords.words("english")

        return [keyword for keyword in keywords if keyword in stopwords_list]

    @staticmethod
    def cos_sim(embedding1, embedding2):
        """
        Computes the cosine similarity between two embeddings.
        """
        import sentence_transformers

        return sentence_transformers.util.cos_sim(embedding1, embedding2)


class TextControlFilter:
    """
    A class that provides methods for filtering control items based on plans.
    """

    @staticmethod
    def control_filter(control_dicts: Dict, plans: List[str]) -> Dict:
        """
        Filters control items based on keywords.
        Args:
            control_dicts (dict): A dictionary of control items to be filtered.
            plans (list): A list of plans for the following steps.
        """
        filtered_control_dict = {}

        keywords = BasicControlFilter.plans_to_keywords(plans)
        for label, control_item in control_dicts.items():
            control_text = control_item.element_info.name.lower()
            if any(
                keyword in control_text or control_text in keyword
                for keyword in keywords
            ):
                filtered_control_dict[label] = control_item
        return filtered_control_dict


class SemanticControlFilter(BasicControlFilter):
    """
    A class that represents a semantic model for control filtering.
    """

    def control_filter_score(self, control_text, plans):
        """
        Calculates the score for a control item based on the similarity between its text and a set of keywords.
        Args:
            control_text (str): The text of the control item.
            plans (list): The plan to be used for calculating the similarity.
        Returns:
            float: The score (0-1) indicating the similarity between the control text and the keywords.
        """
        plan_embedding = self.get_embedding(plans)
        control_text_embedding = self.get_embedding(control_text)
        return max(self.cos_sim(control_text_embedding, plan_embedding).tolist()[0])

    def control_filter(self, control_dicts, plans, top_k):
        """
        Filters control items based on their similarity to a set of keywords.
        Args:
            control_dicts (dict): A dictionary of control items to be filtered.
            plans (list): A list of plans.
            top_k (int): The number of top control items to be selected.
        """
        scores_items = []
        filtered_control_dict = {}

        for label, control_item in control_dicts.items():
            control_text = control_item.element_info.name.lower()
            score = self.control_filter_score(control_text, plans)
            scores_items.append((label, score))
        topk_scores_items = heapq.nlargest(top_k, (scores_items), key=lambda x: x[1])
        topk_items = [
            (score_item[0], score_item[1]) for score_item in topk_scores_items
        ]

        for label, control_item in control_dicts.items():
            if label in topk_items:
                filtered_control_dict[label] = control_item
        return filtered_control_dict


class IconControlFilter(BasicControlFilter):
    """
    A class that represents a icon model for control filtering.
    """

    def control_filter_score(self, control_icon, plans):
        """
        Calculates the score of a control icon based on its similarity to the given keywords.
        Args:
            control_icon: The control icon image.
            plan: The plan to compare the control icon against.
        Returns:
            The maximum similarity score between the control icon and the keywords.
        """
        plans_embedding = self.get_embedding(plans)
        control_icon_embedding = self.get_embedding(control_icon)
        return max(self.cos_sim(control_icon_embedding, plans_embedding).tolist()[0])

    def control_filter(self, control_dicts, cropped_icons_dict, plans, top_k):
        """
        Filters control items based on their scores and returns the top-k items.
        Args:
            control_dicts: The dictionary of all control items.
            cropped_icons: The dictionary of the cropped icons.
            plans: The plans to compare the control icons against.
            top_k: The number of top items to return.
        Returns:
            The list of top-k control items based on their scores.
        """
        scores_items = []
        filtered_control_dict = {}

        for label, cropped_icon in cropped_icons_dict.items():
            score = self.control_filter_score(cropped_icon, plans)
            scores_items.append((score, label))
        topk_scores_items = heapq.nlargest(top_k, scores_items, key=lambda x: x[0])
        topk_labels = [scores_items[1] for scores_items in topk_scores_items]

        for label, control_item in control_dicts.items():
            if label in topk_labels:
                filtered_control_dict[label] = control_item
        return filtered_control_dict
