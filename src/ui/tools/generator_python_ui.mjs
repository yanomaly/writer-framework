/* eslint-disable @typescript-eslint/no-var-requires */
import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";

import * as core from "./core.mjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// eslint-disable-next-line prettier/prettier
const pythonUiPath = path.resolve(__dirname, "..", "..", "streamsync", "ui.py");

const getPyType = (type) => {
	switch (type) {
		case "Number":
			return "Union[float, str]";
		case "Object":
			return "Union[Dict, str]";
		case "Key-Value":
			return "Union[Dict, str]";
		default:
			return "str";
	}
};

/**
 * Loads components from streamsync.
 * @returns {Promise<*>}
 */
async function loadComponents() {
	const rawComponents = await core.loadComponents();
	// eslint-disable-next-line no-console
	return rawComponents.map((component) => {
		return {
			nameTrim: component.name.replaceAll(/\s/g, ""),
			...component,
		};
	});
}

function generateImports() {
	return `from typing import TypedDict, Union, Optional, Dict, Callable
from streamsync.ui_manager import StreamsyncUI
from streamsync.core_ui import Component
  `;
}

function generateTypes(data) {
	const types = data.map((component) => {
		let type = `

${component.nameTrim}Props = TypedDict('${component.nameTrim}Props', {`;
		type += Object.entries(component.fields)
			.map(([key, field]) => {
				return `
    "${key}": ${getPyType(field.type)}`;
			})
			.join(",");
		type += `
}, total=False)`;

		type += `

${component.nameTrim}EventHandlers = TypedDict('${component.nameTrim}EventHandlers', {`;
		type += Object.entries(component.events || {})
			.map(([key]) => {
				return `
    "${key}": Union[str, Callable]`;
			})
			.join(",");
		type += `
}, total=False)`;

		const bindable = Object.entries(component.events || {}).filter(
			([, ev]) => ev.bindable,
		);
		if (!bindable?.length) return type;

		type += `

${component.nameTrim}Bindings = TypedDict('${component.nameTrim}Bindings', {`;
		type += bindable
			.map(([key]) => {
				return `
    "${key}": str`;
			})
			.join(",");
		type += `
}, total=False)`;
		return type;
	});

	return types.join("");
}

function generateClass() {
	return `

class StreamsyncUIManager(StreamsyncUI):
    """The StreamsyncUIManager class is intended to include dynamically-
    generated methods corresponding to UI components defined in the Vue
    frontend during the build process.

    This class serves as a bridge for programmatically interacting with the
    frontend, allowing methods to adapt to changes in the UI components without
    manual updates.
    """
    
    # Hardcoded classes for proof-of-concept purposes
  `;
}

function generateMethods(data) {
	const methods = data.map((component) => {
		const isBindable = Boolean(
			Object.entries(component.events || {}).find(
				([, ev]) => ev.bindable,
			),
		);
		const bindParam = ` 
            binding: Optional[${component.nameTrim}Bindings] = None,`;
		const bindPass = `,
            binding=binding`;
		return `
    @staticmethod
    def ${component.nameTrim}(
            content: ${component.nameTrim}Props = {},
            *,
            id: Optional[str] = None,
            position: Optional[int] = None,
            parentId: Optional[str] = None,
            handlers: Optional[${component.nameTrim}EventHandlers] = None,
            visible: Optional[Union[bool, str]] = None,${isBindable ? bindParam : ""}
            ) -> Component:
        """
        ${component.description}
        """
        component = StreamsyncUI.${component.allowedChildrenTypes?.length ? "create_container_component" : "create_component"}(
            '${component.type}',
            content=content,
            id=id,
            position=position,
            parentId=parentId,
            handlers=handlers,
            visible=visible${isBindable ? bindPass : ""})
        return component
    `;
	});
	return methods.join("");
}

/**
 * Generates the interface file for the low-code ui `ui.py`
 *
 * @returns {Promise<void>}
 */
export async function generate() {
	const components = await loadComponents();

	// eslint-disable-next-line no-console
	console.log("Writing ui.py to", pythonUiPath);
	return fs.writeFile(
		pythonUiPath,
		generateImports() +
			generateTypes(components) +
			generateClass() +
			generateMethods(components),
	);
}
