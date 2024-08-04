# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.


import json
import os
import time
from typing import TYPE_CHECKING, Dict, List, Tuple

from pywinauto.controls.uiawrapper import UIAWrapper

from ufo import utils
from ufo.agents.processors.basic import BaseProcessor
from ufo.automator.ui_control.control_filter import ControlFilterFactory
from ufo.config.config import Config
from ufo.module.context import Context, ContextNames
from copy import deepcopy
if TYPE_CHECKING:
    from ufo.agents.agent.app_agent import AppAgent

configs = Config.get_instance().config_data
BACKEND = configs["CONTROL_BACKEND"]


class AppAgentProcessor(BaseProcessor):
    """
    The processor for the app agent at a single step.
    """

    def __init__(self, agent: "AppAgent", context: Context) -> None:
        """
        Initialize the app agent processor.
        :param agent: The app agent who executes the processor.
        :param context: The context of the session.
        """

        super().__init__(agent=agent, context=context)

        self.app_agent = agent
        self.host_agent = agent.host

        self._annotation_dict = None
        self._control_info = None
        self._operation = None
        self._args = None
        self._image_url = []
        self.control_filter_factory = ControlFilterFactory()
        self.filtered_annotation_dict = None

    @property
    def action(self) -> str:
        """
        Get the action.
        :return: The action.
        """
        return self._action

    @action.setter
    def action(self, action: str) -> None:
        """
        Set the action.
        :param action: The action.
        """
        self._action = action

    def print_step_info(self) -> None:
        """
        Print the step information.
        """
        utils.print_with_color(
            "Round {round_num}, Step {step}, AppAgent: Completing the subtask [{subtask}] on application [{application}].".format(
                round_num=self.round_num + 1,
                step=self.round_step + 1,
                subtask=self.subtask,
                application=self.application_process_name,
            ),
            "magenta",
        )

    def capture_screenshot(self) -> None:
        """
        Capture the screenshot.
        """
        # Define the paths for the screenshots saved.
        screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
        annotated_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_annotated.png"
        )
        concat_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_concat.png"
        )

        self._memory_data.set_values_from_dict(
            {
                "CleanScreenshot": screenshot_save_path,
                "AnnotatedScreenshot": annotated_screenshot_save_path,
                "ConcatScreenshot": concat_screenshot_save_path,
            }
        )

        # Get the control elements in the application window if the control items are not provided for reannotation.
        if type(self.control_reannotate) == list and len(self.control_reannotate) > 0:
            control_list = self.control_reannotate
        else:
            start_time = time.time()
            control_list = self.control_inspector.find_control_elements_in_descendants(
                self.application_window,
                control_type_list=configs["CONTROL_LIST"],
                class_name_list=configs["CONTROL_LIST"],
            )
            end_time = time.time()
            self.log_time("find_control_elements_in_descendants",start_time,end_time)

        start_time = time.time()
        # Get the annotation dictionary for the control items, in a format of {control_label: control_element}.
        self._annotation_dict = self.photographer.get_annotation_dict(
            self.application_window, control_list, annotation_type="number"
        )
        end_time = time.time()
        self.log_time("get_annotation_dict",start_time,end_time)

        start_time = time.time()
        # Attempt to filter out irrelevant control items based on the previous plan.
        self.filtered_annotation_dict = self.get_filtered_annotation_dict(
            self._annotation_dict
        )
        end_time = time.time()
        self.log_time("get_filtered_annotation_dict",start_time,end_time)

        start_time = time.time()
        self.photographer.capture_app_window_screenshot(
            self.application_window, save_path=screenshot_save_path
        )
        end_time = time.time()
        self.log_time("capture_app_window_screenshot",start_time,end_time)

        start_time = time.time()
        # Capture the screenshot of the selected control items with annotation and save it.
        self.photographer.capture_app_window_screenshot_with_annotation_dict(
            self.application_window,
            self.filtered_annotation_dict,
            annotation_type="number",
            save_path=annotated_screenshot_save_path,
        )
        end_time = time.time()
        self.log_time("capture_app_window_screenshot_with_annotation_dict",start_time,end_time)


        start_time = time.time()
        # If the configuration is set to include the last screenshot with selected controls tagged, save the last screenshot.
        if configs["INCLUDE_LAST_SCREENSHOT"]:
            last_screenshot_save_path = (
                self.log_path + f"action_step{self.session_step - 1}.png"
            )
            last_control_screenshot_save_path = (
                self.log_path
                + f"action_step{self.session_step - 1}_selected_controls.png"
            )
            self._image_url += [
                self.photographer.encode_image_from_path(
                    last_control_screenshot_save_path
                    if os.path.exists(last_control_screenshot_save_path)
                    else last_screenshot_save_path
                )
            ]
        end_time = time.time()
        self.log_time("INCLUDE_LAST_SCREENSHOT",start_time,end_time)
        
        start_time = time.time()
        # Whether to concatenate the screenshots of clean screenshot and annotated screenshot into one image.
        if configs["CONCAT_SCREENSHOT"]:
            self.photographer.concat_screenshots(
                screenshot_save_path,
                annotated_screenshot_save_path,
                concat_screenshot_save_path,
            )
            self._image_url += [
                self.photographer.encode_image_from_path(concat_screenshot_save_path)
            ]
        else:
            screenshot_url = self.photographer.encode_image_from_path(
                screenshot_save_path
            )
            screenshot_annotated_url = self.photographer.encode_image_from_path(
                annotated_screenshot_save_path
            )
            self._image_url += [screenshot_url, screenshot_annotated_url]
        end_time = time.time()
        self.log_time("CONCAT_SCREENSHOT",start_time,end_time)

        # Save the XML file for the current state.
        if configs["LOG_XML"]:
            start_time = time.time()
            self._save_to_xml()
            end_time = time.time()
            self.log_time("LOG_XML",start_time,end_time)
        

    def get_control_info(self) -> None:
        """
        Get the control information.
        """
        start_time = time.time()
        control_type_field_name = "control_type" if BACKEND == "uia" else "control_class"
        # Get the control information for the control items and the filtered control items, in a format of list of dictionaries.
        self._control_info = self.control_inspector.get_control_info_list_of_dict(
            self._annotation_dict,
            ["control_text", control_type_field_name,"selected"],
        )
        end_time = time.time()
        self.log_time("get_control_info_list_of_dict", start_time, end_time)

        # print(f"Temp control info: {json.dumps(self._control_info)}")
        
        # modify the fields to align lam
        _fix_control_info = []
        for control_info in self._control_info:
            control_info["text"] = control_info["control_text"]
            del control_info["control_text"]

            control_info["type"] = control_info[control_type_field_name]
            del control_info[control_type_field_name]
            _fix_control_info.append(control_info)

        self._control_info = _fix_control_info

        start_time = time.time()
        self.filtered_control_info = (
            self.control_inspector.get_control_info_list_of_dict(
                self.filtered_annotation_dict,
                [
                    "control_text",
                    control_type_field_name,
                    "selected"
                ],
            )
        )
        end_time = time.time()
        self.log_time("filter get_control_info_list_of_dict", start_time, end_time)

        
        _fix_filtered_control_info = []
        for control_info in self.filtered_control_info:

            control_info["text"] = control_info["control_text"]
            del control_info["control_text"]
            control_info["type"] = control_info[control_type_field_name]
            del control_info[control_type_field_name]
            _fix_filtered_control_info.append(control_info)

        self.filtered_control_info = _fix_filtered_control_info

    def get_prompt_message(self) -> None:
        """
        Get the prompt message for the AppAgent.
        """

        examples, tips = self.demonstration_prompt_helper()

        # Get the external knowledge prompt for the AppAgent using the offline and online retrievers.
        external_knowledge_prompt = self.app_agent.external_knowledge_prompt_helper(
            self.request,
            configs["RAG_OFFLINE_DOCS_RETRIEVED_TOPK"],
            configs["RAG_ONLINE_RETRIEVED_TOPK"],
        )

        if configs["LAM_TEMPLATE_VERSION"] == 4:
            step_history = [] if not self.app_agent.memory.get_latest_item() else self.app_agent.memory.get_latest_item().to_dict().get("step_history", [])
            self._prompt_message = self.app_agent.lam_message_constructor(
                control_info=self.filtered_control_info,
                request=self.request,
                step_history=step_history,
            )
        elif configs["LAM_TEMPLATE_VERSION"] == 2:
            # "step" not the same with version 4
            step_history = []  if not self.app_agent.memory.get_latest_item() else self.app_agent.memory.get_latest_item().to_dict().get("step_history", [])
            previous_plan = [] if not self.app_agent.memory.get_latest_item() else self.app_agent.memory.get_latest_item().to_dict().get("previous_plan", [])
            self._prompt_message = self.app_agent.lam_message_constructor(
                control_info=self.filtered_control_info,
                request=self.request,
                step_history=step_history,
                previous_plan=previous_plan
            )
        # Log the prompt message. Only save them in debug mode.
        log = json.dumps(
            {
                "step": self.session_step,
                "prompt": self._prompt_message,
                "control_items": self._control_info,
                "filted_control_items": self.filtered_control_info,
                "status": "",
            }
        )
        self.request_logger.debug(log)

    def get_response(self) -> None:
        """
        Get the response from the LLM.
        """
        # Try to get the response from the LLM. If an error occurs, catch the exception and log the error.
        try:
            self._response, self.cost = self.app_agent.get_response(
                self._prompt_message, "APPAGENT", use_backup_engine=True
            )
        except Exception:
            self.llm_error_handler()
            return

    def parse_response(self) -> None:
        """
        Parse the response.
        """

        # Try to parse the response. If an error occurs, catch the exception and log the error.
        try:
            self._response_json = self.app_agent.response_to_dict(self._response)

        except Exception:
            self.general_error_handler()

        self._control_label = self._response_json.get("control_label", "")
        self.control_text = self._response_json.get("control_name", "")
        self._operation = self._response_json.get("function", "")
        self._args = utils.revise_line_breaks(self._response_json.get("args", ""))

        # Compose the function call and the arguments string.
        self.action = self.app_agent.Puppeteer.get_command_string(
            self._operation, self._args
        )

        self.status = self._response_json.get("status", "")

        # don't work
        self.question_list = self._response_json.get("Questions", [])
        # # Convert the plan from a string to a list if the plan is a string.
        self.plan = self.string2list(self._response_json.get("Plan", ""))
        self._response_json["Plan"] = self.plan

        self.app_agent.print_response(self._response_json)

    def action_mapping(self)->None:
        """
        Mapping the action to the UFO action
        """
        map_dict = {
            "Type_keys":{
                "function":"keyboard_input",
                "args":{
                    "keys":"keys"
                }
            }
        }

        if self._operation in map_dict:
            self._operation = map_dict[self._operation]["function"]
            for key in map_dict[self._operation]["args"]:
                ori_value = self._args[key]
                del self._args[key]
                self._args[map_dict[self._operation]["args"][key]] = ori_value  

    def execute_action(self) -> None:
        """
        Execute the action.
        """

        try:
            # mapping the action first
            self.action_mapping()


            # Get the selected control item from the annotation dictionary and LLM response.
            # The LLM response is a number index corresponding to the key in the annotation dictionary.
            control_selected = self._annotation_dict.get(self._control_label, "")

            if configs.get("SHOW_VISUAL_OUTLINE_ON_SCREEN", True) and control_selected:
                control_selected.draw_outline(colour="red", thickness=3)
                time.sleep(configs.get("RECTANGLE_TIME", 0))

            self.app_agent.Puppeteer.receiver_manager.create_ui_control_receiver(
                control_selected, self.application_window
            )

            # Save the screenshot of the tagged selected control.
            self.capture_control_screenshot(control_selected)

            if self.status.upper() == self._agent_status_manager.SCREENSHOT.value:
                self.handle_screenshot_status()
            else:
                self._results = self.app_agent.Puppeteer.execute_command(
                    self._operation, self._args
                )
                self.control_reannotate = None
            if not utils.is_json_serializable(self._results):
                self._results = ""

                return

        except Exception:
            self.general_error_handler()

    def capture_control_screenshot(self, control_selected: UIAWrapper) -> None:
        """
        Capture the screenshot of the selected control.
        :param control_selected: The selected control item.
        """
        control_screenshot_save_path = (
            self.log_path + f"action_step{self.session_step}_selected_controls.png"
        )

        self._memory_data.set_values_from_dict(
            {"SelectedControlScreenshot": control_screenshot_save_path}
        )
        self.photographer.capture_app_window_screenshot_with_rectangle(
            self.application_window,
            sub_control_list=[control_selected],
            save_path=control_screenshot_save_path,
        )

    def handle_screenshot_status(self) -> None:
        """
        Handle the screenshot status when the annotation is overlapped and the agent is unable to select the control items.
        """

        utils.print_with_color(
            "Annotation is overlapped and the agent is unable to select the control items. New annotated screenshot is taken.",
            "magenta",
        )
        self.control_reannotate = self.app_agent.Puppeteer.execute_command(
            "annotation", self._args, self._annotation_dict
        )
    
    def parse_lam_steps(self,response_json)->dict:
        """
        Parse the steps in LAM for 'step_history'
        """
        step_json = {}
        step_json['action']={}
        if configs["LAM_TEMPLATE_VERSION"] == 4:
            step_json["plan"] = response_json.get("thought", "")
        step_json['action']["control_name"] = response_json.get("control_name", "")
        step_json['action']['control_id'] = response_json.get("control_label","")
        step_json['action']['function'] = response_json.get("function","")
        step_json['action']['args'] = response_json.get("args","")
        return step_json


    def update_memory(self) -> None:
        """
        Update the memory of the Agent.
        """

        app_root = self.control_inspector.get_application_root_name(
            self.application_window
        )

        # Log additional information for the app agent.
        additional_memory = {
            "Step": self.session_step,
            "RoundStep": self.round_step,
            "AgentStep": self.app_agent.step,
            "Round": self.round_num,
            "Subtask": self.subtask,
            "SubtaskIndex": self.round_subtask_amount,
            "Action": self.action,
            "ActionType": self.app_agent.Puppeteer.get_command_types(self._operation),
            "Request": self.request,
            "Agent": "ActAgent",
            "AgentName": self.app_agent.name,
            "Application": app_root,
            "Cost": self._cost,
            "Results": self._results,
        }

        # merge the history response list
        if configs["LAM_TEMPLATE_VERSION"]==4:
            if self.app_agent.memory.get_latest_item():
                step_history =  self.app_agent.memory.get_latest_item().to_dict().get("step_history", [])
            else:
                step_history = []
            self._memory_data.set_values_from_dict({"step_history": step_history + [self.parse_lam_steps(self._response_json)]})
        elif configs["LAM_TEMPLATE_VERSION"]==2:
            if self.app_agent.memory.get_latest_item():
                step_history =  self.app_agent.memory.get_latest_item().to_dict().get("step_history", [])
            else:
                step_history = []
            self._memory_data.set_values_from_dict({"step_history": step_history + [self.parse_lam_steps(self._response_json)]})
            self._memory_data.set_values_from_dict({"previous_plan": self._response_json.get("plan",[])})
        self._memory_data.set_values_from_dict(self._response_json)
        self._memory_data.set_values_from_dict(additional_memory)

        if self.status.upper() == self._agent_status_manager.CONFIRM.value:
            self._memory_data.set_values_from_dict({"UserConfirm": "Yes"})

        self.app_agent.add_memory(self._memory_data)

        # Log the memory item.
        self.context.add_to_structural_logs(self._memory_data.to_dict())
        self.log(self._memory_data.to_dict())

        # Only memorize the keys in the HISTORY_KEYS list to feed into the prompt message in the future steps.
        memorized_action = {
            key: self._memory_data.to_dict().get(key) for key in configs["HISTORY_KEYS"]
        }

        if self.is_confirm():

            if self._is_resumed:
                self._memory_data.set_values_from_dict({"UserConfirm": "Yes"})
                memorized_action["UserConfirm"] = "Yes"
            else:
                self._memory_data.set_values_from_dict({"UserConfirm": "No"})
                memorized_action["UserConfirm"] = "No"

        # Save the screenshot to the blackboard if the SaveScreenshot flag is set to True by the AppAgent.
        self._update_image_blackboard()
        self.host_agent.blackboard.add_trajectories(memorized_action)

    def _update_image_blackboard(self) -> None:
        """
        Save the screenshot to the blackboard if the SaveScreenshot flag is set to True by the AppAgent.
        """
        screenshot_saving = self._response_json.get("SaveScreenshot", {})

        if screenshot_saving.get("save", False):

            screenshot_save_path = self.log_path + f"action_step{self.session_step}.png"
            metadata = {
                "screenshot application": self.context.get(
                    ContextNames.APPLICATION_PROCESS_NAME
                ),
                "saving reason": screenshot_saving.get("reason", ""),
            }
            self.app_agent.blackboard.add_image(screenshot_save_path, metadata)

    def _save_to_xml(self) -> None:
        """
        Save the XML file for the current state. Only work for COM objects.
        """
        log_abs_path = os.path.abspath(self.log_path)
        xml_save_path = os.path.join(
            log_abs_path, f"xml/action_step{self.session_step}.xml"
        )
        self.app_agent.Puppeteer.save_to_xml(xml_save_path)

    def demonstration_prompt_helper(self) -> Tuple[List[str], List[str]]:
        """
        Get the examples and tips for the AppAgent using the demonstration retriever.
        :return: The examples and tips for the AppAgent.
        """

        # Get the examples and tips for the AppAgent using the experience and demonstration retrievers.
        if configs["RAG_EXPERIENCE"]:
            experience_examples, experience_tips = (
                self.app_agent.rag_experience_retrieve(
                    self.request, configs["RAG_EXPERIENCE_RETRIEVED_TOPK"]
                )
            )
        else:
            experience_examples = []
            experience_tips = []

        if configs["RAG_DEMONSTRATION"]:
            demonstration_examples, demonstration_tips = (
                self.app_agent.rag_demonstration_retrieve(
                    self.request, configs["RAG_DEMONSTRATION_RETRIEVED_TOPK"]
                )
            )
        else:
            demonstration_examples = []
            demonstration_tips = []

        examples = experience_examples + demonstration_examples
        tips = experience_tips + demonstration_tips

        return examples, tips

    def get_filtered_annotation_dict(
        self, annotation_dict: Dict[str, UIAWrapper]
    ) -> Dict[str, UIAWrapper]:
        """
        Get the filtered annotation dictionary.
        :param annotation_dict: The annotation dictionary.
        :return: The filtered annotation dictionary.
        """

        # Get the control filter type and top k plan from the configuration.
        control_filter_type = configs["CONTROL_FILTER_TYPE"]
        topk_plan = configs["CONTROL_FILTER_TOP_K_PLAN"]

        if len(control_filter_type) == 0 or self.prev_plan == []:
            return annotation_dict

        control_filter_type_lower = [
            control_filter_type_lower.lower()
            for control_filter_type_lower in control_filter_type
        ]

        filtered_annotation_dict = {}

        # Get the top k recent plans from the memory.
        plans = self.control_filter_factory.get_plans(self.prev_plan, topk_plan)

        # Filter the annotation dictionary based on the keywords of control text and plan.
        if "text" in control_filter_type_lower:
            model_text = self.control_filter_factory.create_control_filter("text")
            filtered_text_dict = model_text.control_filter(annotation_dict, plans)
            filtered_annotation_dict = (
                self.control_filter_factory.inplace_append_filtered_annotation_dict(
                    filtered_annotation_dict, filtered_text_dict
                )
            )

        # Filter the annotation dictionary based on the semantic similarity of the control text and plan with their embeddings.
        if "semantic" in control_filter_type_lower:
            model_semantic = self.control_filter_factory.create_control_filter(
                "semantic", configs["CONTROL_FILTER_MODEL_SEMANTIC_NAME"]
            )
            filtered_semantic_dict = model_semantic.control_filter(
                annotation_dict, plans, configs["CONTROL_FILTER_TOP_K_SEMANTIC"]
            )
            filtered_annotation_dict = (
                self.control_filter_factory.inplace_append_filtered_annotation_dict(
                    filtered_annotation_dict, filtered_semantic_dict
                )
            )

        # Filter the annotation dictionary based on the icon image icon and plan with their embeddings.
        if "icon" in control_filter_type_lower:
            model_icon = self.control_filter_factory.create_control_filter(
                "icon", configs["CONTROL_FILTER_MODEL_ICON_NAME"]
            )

            cropped_icons_dict = self.photographer.get_cropped_icons_dict(
                self.application_window, annotation_dict
            )
            filtered_icon_dict = model_icon.control_filter(
                annotation_dict,
                cropped_icons_dict,
                plans,
                configs["CONTROL_FILTER_TOP_K_ICON"],
            )
            filtered_annotation_dict = (
                self.control_filter_factory.inplace_append_filtered_annotation_dict(
                    filtered_annotation_dict, filtered_icon_dict
                )
            )

        return filtered_annotation_dict
