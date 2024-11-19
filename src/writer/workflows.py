import time
from typing import Any, Dict, List, Literal, Optional, Tuple, Type

from writer.ss_types import WorkflowExecutionLog
from typing import Dict, List
from writer.ss_types import InstancePath

WorkflowBlock_T = Type["WorkflowBlock"]
block_map:Dict[str, WorkflowBlock_T] = {}

import writer.core
from writer.core import WriterSession, Component

class WorkflowRunner():

    def __init__(self, session: WriterSession):
        import writer.blocks

        self.execution: Dict[str, WorkflowBlock] = {}
        self.state = session.session_state
        self.component_tree = session.session_component_tree
        self.evaluator = writer.evaluator.Evaluator(session)

    def run_workflow_by_key(self, workflow_key: str, execution_environment: Dict = {}):
        all_components = self.component_tree.components.values()
        workflows = list(filter(lambda c: c.type == "workflows_workflow" and c.content.get("key") == workflow_key, all_components))
        if len(workflows) == 0:
            raise ValueError(f'Workflow with key "{workflow_key}" not found.')
        workflow = workflows[0]
        return self.run_workflow(workflow.id, execution_environment)

    def _get_workflow_nodes(self, component_id):
        return self.component_tree.get_descendents(component_id)

    def _get_branch_nodes(self, base_component_id: str, base_outcome: str):
        base_component = self.component_tree.get_component(base_component_id)
        if not base_component:
            raise RuntimeError(f'Cannot obtain branch. Could not find component "{base_component_id}".')
        outs = base_component.outs
        nodes:List["Component"] = []
        if not outs:
            return nodes
        for out in outs:
            if out.get("outId") == base_outcome:
                component_id = out.get("toNodeId")
                component = self.component_tree.get_component(component_id)
                if not component:
                    continue
                nodes.append(component)
        return nodes

    def run_branch(self, base_component_id: str, base_outcome: str, execution_environment: Dict):
        nodes = self._get_branch_nodes(base_component_id, base_outcome)
        return self.run_nodes(nodes, execution_environment)

    def run_workflow(self, component_id: str, execution_environment):
        nodes = self._get_workflow_nodes(component_id)
        return self.run_nodes(nodes, execution_environment)

    def run_nodes(self, nodes: List["Component"], execution_environment: Dict):
        execution: Dict[str, WorkflowBlock] = {}
        return_value = None
        try:
            for node in self.get_terminal_nodes(nodes):
                self.run_node(node, nodes, execution_environment)
            for tool in execution.values():
                if tool and tool.return_value is not None:
                    return_value = tool.return_value
        except BaseException as e:
            self._generate_run_log("Failed workflow execution", "error")
            raise e
        else:
            self._generate_run_log("Workflow execution", "info", return_value)
        return return_value

    def _generate_run_log(self, title: str, entry_type: Literal["info", "error"], return_value: Optional[Any] = None):
        if not writer.core.Config.is_mail_enabled_for_log:
            return
        exec_log:WorkflowExecutionLog = WorkflowExecutionLog(summary=[])
        for component_id, tool in self.execution.items():
            exec_log.summary.append({
                "componentId": component_id,
                "outcome": tool.outcome,
                "result": tool.result,
                "returnValue": tool.return_value,
                "executionEnvironment": tool.execution_environment,
                "executionTimeInSeconds": tool.execution_time_in_seconds 
            })
        msg = "Execution finished."
        self.state.add_log_entry(entry_type, title, msg, workflow_execution=exec_log)


    def get_terminal_nodes(self, nodes):
        return [node for node in nodes if not node.outs]

    def _get_node_dependencies(self, target_node: "Component", nodes: List["Component"]):
        dependencies:List[Tuple] = []
        parent_id = target_node.parentId
        if not parent_id:
            return []
        for node in nodes:
            if not node.outs:
                continue
            for out in node.outs:
                to_node_id = out.get("toNodeId")
                out_id = out.get("outId")
                if to_node_id == target_node.id:
                    dependencies.append((node, out_id))
        return dependencies

    def _is_outcome_managed(self, target_node: "Component", target_out_id: str):
        if not target_node.outs:
            return False
        for out in target_node.outs:
            if out.get("outId") == target_out_id:
                return True
        return False

    def run_node(self, target_node: "Component", nodes: List["Component"], execution_environment: Dict):
        tool_class = block_map.get(target_node.type)
        if not tool_class:
            raise RuntimeError(f'Could not find tool for "{target_node.type}".')
        dependencies = self._get_node_dependencies(target_node, nodes)

        tool = self.execution.get(target_node.id)
        if tool:
            return tool

        result = None
        matched_dependencies = 0
        for node, out_id in dependencies:
            tool = self.run_node(node, nodes, execution_environment)
            if not tool:
                continue
            if tool.outcome == out_id:
                matched_dependencies += 1
            result = tool.result
            if tool.return_value is not None:
                return

        if len(dependencies) > 0 and matched_dependencies == 0:
            return

        expanded_execution_environment = execution_environment | {
            "result": result,
            "results": { k:v.result for k,v in self.execution.items() }
        }
        tool = tool_class(target_node, self, expanded_execution_environment)
        
        try:
            start_time = time.time()
            tool.run()
            tool.execution_time_in_seconds = time.time() - start_time
        except BaseException as e:
            if tool and not tool.result:
                tool.result = repr(e)
            if not tool.outcome or not self._is_outcome_managed(target_node, tool.outcome):
                raise e
        finally:
            self.execution[target_node.id] = tool
        
        return tool

class WorkflowBlock:
    
    @classmethod
    def register(cls, type: str):
        block_map[type] = cls

    def __init__(self, component: "Component", runner: WorkflowRunner, execution_environment: Dict):
        self.outcome = None
        self.component = component
        self.runner = runner
        self.execution_time_in_seconds = -1.0
        self.execution_environment = execution_environment
        self.result:Any = None
        self.return_value = None
        self.instance_path: InstancePath = [{"componentId": self.component.id, "instanceNumber": 0}]

    def _get_field(self, field_key: str, as_json=False, default_field_value=None):
        if default_field_value is None:
            if as_json:
                default_field_value = "{}"
            else:
                default_field_value = ""
        value = self.runner.evaluator.evaluate_field(self.instance_path, field_key, as_json, default_field_value, self.execution_environment)
        return value

    def _set_state(self, expr: str, value: Any):
        self.runner.evaluator.set_state(expr, self.instance_path, value, base_context=self.execution_environment)

    def run(self):
        pass