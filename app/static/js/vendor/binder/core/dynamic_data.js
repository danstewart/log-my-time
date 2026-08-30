import { DynamicFrame } from "./dynamic_frame.js";

/*
This is a subset of DynamicFrame that fetches data (eg. from a JSON API)
and renders it in a template.

Example HTML:
<dynamic-data :url="/some/url" :param-day="Monday">
    <p :render>Sales for Monday: ${data.sales.total}</p>
</dynamic-data>
*/

/**
 * @class
 * @name DynamicData
 * @namespace DynamicData
 * @property url - The URL to fetch
 * @property mode - The mode to use for adding the response content, either `replace`, `append` or `prepend` (Defaults to `replace`)
 * @property mountPoint - A selector used to find the element to mount to within the element (defaults to the root element)
 * @property autoRefresh - Will call `refresh()` automatically at the specified interval (Intervals are in the format `${num}${unit}` where unit is one of ms, s, m, h: `10s` = 10 seconds)
 * @property delay - An artificial delay applied before displaying the content
 * @property stateKey - An optional key, if specified the frame state will be stored and loaded from the page query string
 * @property contained - If `true` then the frame will be self contained, clicking links and submitting forms will be handled within the frame and **not** impact the surrounding page
 * @example
 *  <dynamic-data :url="/some/url" :param-day="Monday" :mount-point=".content">
 *      <p :render>Sales for Monday: ${data.sales.total}</p>
 *  </dynamic-data>
 */
class DynamicData extends DynamicFrame {
    // TODO
    /**
     * Actually updates the content
     * This is where the artificial delay is applied
     * @param content - The content to use
     * @param mode - replace or append, defaults to `this.args.mode`
     * @memberof! DynamicFrame
     */
    updateContent(content, mode = null) {
        if (!mode) mode = this.args.mode || "replace";

        const template = document.createElement("template");
        template.innerHTML = content;

        // If we want to execute scripts then go through our template and turn script tags into real scripts
        if (this.args.executeScripts) {
            let scripts = template.content.querySelectorAll("script");

            [...scripts].forEach(script => {
                let newScript = document.createElement("script");

                // Copy all attributes to the new script
                [...script.attributes].forEach(attr => newScript.setAttribute(attr.name, attr.value));

                // Copy the content of the script tag
                if (script.innerHTML) newScript.appendChild(document.createTextNode(script.innerHTML));

                // Add the script tag back in
                script.replaceWith(newScript);
            });
        }

        if (mode === "replace") {
            this.mountPoint.replaceChildren(template.content);
        } else if (mode === "append") {
            this.mountPoint.appendChild(template.content);
        } else if (mode === "prepend") {
            this.mountPoint.prepend(template.content);
        }

        this.emit("frame-updated", { from: this, mode: mode });
    }
}

export { DynamicData };
