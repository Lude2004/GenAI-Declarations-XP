// Form
const activityCheckboxes = document.querySelectorAll(".activity-checkbox");
const singleAiToolCheckbox = document.getElementById("id_use_single_ai_tool");
const globalAiTool = document.querySelector(".global-ai-tool");
const singleAiTool = document.querySelector(".single-ai-tool");

document.querySelectorAll("dialog[open]").forEach((dialog) => {
    dialog.close();
});

document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) {
        return;
    }

    const activityName = target.closest(".activity-name");
    if (!activityName) {
        return;
    }

    const checkbox = activityName
        .closest(".phase-card")
        ?.querySelector(".activity-checkbox");
    if (!checkbox) {
        return;
    }

    if (checkbox.dataset.added === "true") {
        return;
    }

    event.preventDefault();
    event.stopPropagation();
    activityName.closest(".phase-card").open = true;
    checkbox.checked = true;
    showActivityFields(checkbox);
});

function clearFields(container) {
    container.querySelectorAll("input, textarea, select").forEach((input) => {
        if (input instanceof HTMLInputElement &&
            (input.type === "radio" || input.type === "checkbox")) {
            input.checked = false;
        } else {
            input.value = "";
        }
    });
}

function getActivityTable(checkbox) {
    return checkbox.closest(".phase-card")?.querySelector(
        `.selected-activities-table[data-activity-fields-id="${CSS.escape(
            checkbox.dataset.fieldsId
        )}"]`
    );
}

function getActivityName(checkbox) {
    const nameInput = checkbox.closest(".phase-card")?.querySelector(
        "input[name$='activity_name']"
    );
    return checkbox.dataset.activityName || nameInput?.value.trim() || "";
}

function getFieldValue(container, fieldName) {
    const fields = [...container.querySelectorAll("input, textarea, select")]
        .filter((field) => field.name.split("-").pop() === fieldName);

    if (!fields.length) {
        return "";
    }

    const radio = fields.find((field) => field.type === "radio" && field.checked);
    if (radio) {
        return radio.value;
    }

    const field = fields[0];
    return field.type === "checkbox"
        ? (field.checked ? field.value : "")
        : field.value.trim();
}

function updateActivityTableVisibility(table) {
    if (table) {
        const hasRows = Boolean(table.querySelector("tbody tr"));
        table.hidden = !hasRows;
        table.classList.toggle("has-activity-data", hasRows);
    }
}

function updatePhaseActivityCounter(phase) {
    if (!phase) {
        return;
    }

    const activities = [...phase.querySelectorAll(".activity-checkbox")]
        .filter((checkbox) => !checkbox.closest(".custom-activity-template"));
    const selectedActivities = activities.filter((checkbox) => checkbox.checked);
    const counter = phase.querySelector(".counter-selected-activities");

    if (counter) {
        counter.textContent = `${selectedActivities.length} / ${activities.length}`;
    }
}

function updateActivityCounters() {
    document.querySelectorAll(".card[data-phase-id]").forEach(
        updatePhaseActivityCounter
    );
}

function addActivityToTable(checkbox) {
    const table = getActivityTable(checkbox);
    const fields = document.getElementById(checkbox.dataset.fieldsId);
    const actionsTemplate = table?.querySelector(".activity-actions-template");

    if (!table || !fields || !actionsTemplate) {
        return;
    }

    const key = `${checkbox.name}:${checkbox.value}`;
    const existingRow = table.querySelector(`[data-activity-key="${CSS.escape(key)}"]`);

    const row = existingRow || document.createElement("tr");
    row.dataset.activityKey = key;
    row.dataset.fieldsId = checkbox.dataset.fieldsId;

    row.replaceChildren(); 

    const values = [];
    const labels = [];

    if (!singleAiToolCheckbox?.checked) {
        values.push(
            getFieldValue(fields, "ai_tool_name"),
            getFieldValue(fields, "ai_model_name"),
            getFieldValue(fields, "ai_model_version"),
            getFieldValue(fields, "type_ai_tool")
        );
        labels.push("Herramienta", "Modelo", "Versión", "Tipo");
    }

    values.push(
        getFieldValue(fields, "input_data"),
        getFieldValue(fields, "description_process"),
        getFieldValue(fields, "human_verification"),
        getFieldValue(fields, "ai_support_level")
    );
    labels.push(
        "Datos de entrada compartidos",
        "Descripción",
        "Verificación humana",
        "Nivel de apoyo"
    );

    const dataCell = document.createElement("td");
    dataCell.className = "activity-data-cell";

    values.forEach((value, index) => {
        const item = document.createElement("div");
        item.className = "activity-data-item";

        const label = document.createElement("strong");
        label.textContent = `${labels[index]}:`;

        const content = document.createElement("span");
        content.textContent = value || "No especificado";

        item.append(label, content);
        dataCell.appendChild(item);
    });

    row.appendChild(dataCell);

    row.appendChild(actionsTemplate.content.cloneNode(true));

    if (!existingRow) {
        table.querySelector("tbody").appendChild(row);
    }

    checkbox.dataset.added = "true";
    checkbox.closest(".custom-activity-card")?.setAttribute("open", "");
    updateActivityTableVisibility(table);
}

function restoreSelectedActivityTables() {
    document.querySelectorAll(
        ".activity-checkbox:checked:not(.custom-activity-template .activity-checkbox)"
    ).forEach((checkbox) => {
        if (checkbox.dataset.fieldsId) {
            addActivityToTable(checkbox);
            checkbox.closest(".phase-card").open = true;
        }
    });
}

restoreSelectedActivityTables();

function removeActivityFromTable(checkbox) {
    const table = getActivityTable(checkbox);
    const key = `${checkbox.name}:${checkbox.value}`;
    const row = table?.querySelector(`[data-activity-key="${CSS.escape(key)}"]`);
    row?.remove();
    delete checkbox.dataset.added;
    updateActivityTableVisibility(table);
}

function validateActivity(checkbox, fields) {
    const requiredNames = [
        "description_process",
        "human_verification",
        "ai_support_level",
    ];
    if (!singleAiToolCheckbox?.checked) {
        requiredNames.push(
            "ai_tool_name",
            "type_ai_tool",
            "ai_model_name"
        );
    }

    const activityCard = checkbox.closest(".phase-card");
    const activityName = activityCard?.querySelector(
        "input[name$='activity_name']"
    );
    const requiredFields = [...fields.querySelectorAll("input, textarea, select")]
        .filter((input) => requiredNames.includes(input.name.split("-").pop()));

    if (activityName) {
        requiredFields.push(activityName);
    }

    requiredFields.forEach((input) => input.setCustomValidity(""));
    const missingField = requiredFields.find((input) => {
        if (input.type === "radio") {
            return !fields.querySelector(
                `input[name="${CSS.escape(input.name)}"]:checked`
            );
        }
        return !input.value.trim();
    });

    if (missingField) {
        missingField.setCustomValidity("Completa este campo antes de agregar la actividad.");
        missingField.reportValidity();
        missingField.focus();
        return false;
    }
    return true;
}

function showActivityFields(checkbox) {
    const fields = document.getElementById(checkbox.dataset.fieldsId);
    const dialog = fields?.querySelector("dialog");

    if (!fields || !dialog) {
        return;
    }

    checkbox.checked = true;
    fields.hidden = false;
    fields.querySelectorAll("input, textarea, select").forEach((input) => {
        input.disabled = false;
    });
    updateActivityToolVisibility();

    if (!dialog.open) {
        dialog.showModal();
    }
}

function closeModal(button) {
    const dialog = button.closest("dialog");
    const fields = dialog?.closest(".activity-fields");
    const activityCard = fields?.closest(".phase-card");
    const checkbox = activityCard?.querySelector(".activity-checkbox");

    dialog?.close();

    if (checkbox) {
        if (checkbox.dataset.added === "true") {
            delete checkbox.dataset.editing;
            if (fields) {
                fields.hidden = true;
            }
            return;
        }

        checkbox.checked = false;
        clearFields(fields);
        checkbox.dispatchEvent(new Event("change", { bubbles: true }));
    }

    if (fields) {
        fields.hidden = true;
    }
}

function clearAllAiData() {
    clearSingleAiToolFields();

    document.querySelectorAll(".activity-fields").forEach((fields) => {
        fields.querySelector("dialog")?.close();
        clearFields(fields);
        fields.hidden = true;
        fields.querySelectorAll("input, textarea, select").forEach((input) => {
            input.disabled = true;
        });

        const customActivityName = fields.closest(".custom-activity-card")
            ?.querySelector(".custom-activity-name");
        if (customActivityName) {
            customActivityName.textContent = "";
        }
    });

    document.querySelectorAll(".activity-checkbox").forEach((checkbox) => {
        checkbox.checked = false;
        delete checkbox.dataset.added;
        delete checkbox.dataset.editing;

        const table = getActivityTable(checkbox);
        table?.querySelector("tbody")?.replaceChildren();
        updateActivityTableVisibility(table);
    });

    updateActivityCounters();
}

function updateSingleAiToolMode() {
    const enabled = singleAiToolCheckbox?.checked ?? false;
    const requiredGlobalFields = new Set([
        "global_ai_tool_name",
        "global_type_ai_tool",
        "global_ai_model_name",
    ]);

    if (singleAiTool) {
        singleAiTool.hidden = !enabled;
    }

    if (globalAiTool) {
        globalAiTool.hidden = !enabled;

        globalAiTool.querySelectorAll("input, textarea, select").forEach((input) => {
            input.disabled = !enabled;
            const isRequired = enabled &&
                requiredGlobalFields.has(input.name);
            input.required = isRequired;
            const fieldContainer = input.closest(
                ".tool-name-field, .model-name-field, .tool-type"
            );
            const label = fieldContainer?.querySelector(":scope > label");
            label?.classList.toggle("required", isRequired);

            if (!enabled) {
                if (input instanceof HTMLInputElement &&
                    (input.type === "radio" || input.type === "checkbox")) {
                    input.checked = false;
                } else {
                    input.value = "";
                }
            }
        });
    }

    document.querySelectorAll(".ai-tool").forEach((tool) => {
        tool.hidden = enabled;
        tool.classList.toggle("single-tool-hidden", enabled);

        const activityFields = tool.closest(".activity-fields");
        const activityCheckbox = activityFields?.previousElementSibling
            ?.querySelector(".activity-checkbox");
        const disabled = enabled || !(activityCheckbox?.checked ?? false);

        tool.querySelectorAll("input, textarea, select").forEach((input) => {
            input.disabled = disabled;
        });
    });

}

function updateActivityToolVisibility() {
    const enabled = singleAiToolCheckbox?.checked ?? false;
    document.querySelectorAll(".ai-tool").forEach((tool) => {
        tool.hidden = enabled;
        tool.classList.toggle("single-tool-hidden", enabled);
        const activityFields = tool.closest(".activity-fields");
        const activityCheckbox = activityFields?.previousElementSibling
            ?.querySelector(".activity-checkbox");
        const disabled = enabled || !(activityCheckbox?.checked ?? false);
        tool.querySelectorAll("input, textarea, select").forEach((input) => {
            input.disabled = disabled;
        });
    });
}

function bindActivityCheckbox(checkbox, activityFields) {
    checkbox.addEventListener("change", () => {
        const inputs = activityFields.querySelectorAll("input, textarea");
        activityFields.hidden = !checkbox.checked;
        inputs.forEach((input) => {
            input.disabled = !checkbox.checked;
        });
        updateActivityToolVisibility();
        if (checkbox.checked) {
            showActivityFields(checkbox);
        } else {
            activityFields.querySelector("dialog")?.close();
            clearFields(activityFields);
            const customActivityName = activityFields.closest(".custom-activity-card")
                ?.querySelector(".custom-activity-name");
            if (customActivityName) {
                customActivityName.textContent = "";
            }
            removeActivityFromTable(checkbox);
        }
        updatePhaseActivityCounter(checkbox.closest(".card"));
    });
}

activityCheckboxes.forEach((checkbox) => {
    const activityFields = document.getElementById(
        checkbox.dataset.fieldsId || `fields_${checkbox.value}`
    );

    if (!activityFields) {
        return;
    }

    const inputs = activityFields.querySelectorAll("input, textarea");

    activityFields.hidden = !checkbox.checked;
    inputs.forEach((input) => {
        input.disabled = !checkbox.checked;
    });

    bindActivityCheckbox(checkbox, activityFields);
});

updateActivityCounters();

document.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) {
        return;
    }

    const fields = button.closest(".activity-fields");
    if (fields && button.dataset.action === "save-ai-process") {
        const checkbox = fields.closest(".phase-card")?.querySelector(
            ".activity-checkbox"
        );
        if (checkbox) {
            if (!validateActivity(checkbox, fields)) {
                return;
            }
            addActivityToTable(checkbox);
            delete checkbox.dataset.editing;
            fields.hidden = true;
            button.closest("dialog")?.close();
            updatePhaseActivityCounter(checkbox.closest(".card"));
        }
        return;
    }

    if (fields && button.dataset.action === "cancel-activity") {
        const checkbox = fields.closest(".phase-card")?.querySelector(
            ".activity-checkbox"
        );
        if (checkbox) {
            if (checkbox.dataset.added === "true") {
                delete checkbox.dataset.editing;
                fields.hidden = true;
                return;
            }
            checkbox.checked = false;
            clearFields(fields);
            removeActivityFromTable(checkbox);
        }
        fields.hidden = true;
        return;
    }

    const row = button.closest("tr[data-activity-key]");
    if (!row) {
        return;
    }
    const checkbox = [...document.querySelectorAll(".activity-checkbox")]
        .find((item) => `${item.name}:${item.value}` === row.dataset.activityKey);
    if (!checkbox) {
        return;
    }
    if (button.dataset.action === "edit-activity") {
        checkbox.dataset.editing = "true";
        showActivityFields(checkbox);
    } else if (button.dataset.action === "delete-activity") {
        checkbox.checked = false;
        checkbox.dispatchEvent(new Event("change", { bubbles: true }));
        const customActivity = checkbox.closest(".custom-activity-card");
        const customActivityList = customActivity?.closest(
            ".custom-activity-list"
        );
        if (customActivity && customActivityList) {
            removeCustomActivityCard(customActivity, customActivityList);
        }
    }
});

document.querySelector("form")?.addEventListener("submit", (event) => {
    document.querySelectorAll("dialog[open]").forEach((dialog) => {
        dialog.close();
    });

    document.querySelectorAll(".activity-fields").forEach((fields) => {
        fields.querySelectorAll("input, textarea, select").forEach((input) => {
            input.disabled = false;
        });
    });

    const tables = document.querySelectorAll(
        "form .selected-activities-table"
    );
    const rows = [...tables].flatMap((table) => [
        ...table.querySelectorAll("tbody tr[data-activity-key]"),
    ]).filter((row) => !row.closest(".custom-activity-template"));
    if (!rows.length) {
        event.preventDefault();
        document.querySelector("#declaration")?.replaceChildren(
            Object.assign(document.createElement("p"), {
                textContent: "Agrega al menos una actividad asistida con IAG antes de generar la declaración.",
            })
        );
        alert("Agrega al menos una actividad asistida con IAG antes de generar la declaración.");
        return;
    }

    const inputsContainer = document.getElementById("added-activities-inputs");
    inputsContainer.replaceChildren();
    rows.forEach((row) => {
        const [name, value] = row.dataset.activityKey.split(":");
        const input = document.createElement("input");
        input.type = "hidden";
        input.name = name === "activities"
            ? "added_activities"
            : "added_custom_activities";
        input.value = value;
        inputsContainer.appendChild(input);
    });
});

const singleAiToolDialog = document.getElementById("dlg");
const keepSingleAiToolButton = document.getElementById("dno");
const removeSingleAiToolButton = document.getElementById("dyes");

function clearSingleAiToolFields() {
    globalAiTool?.querySelectorAll("input, textarea, select").forEach((input) => {
        if (input instanceof HTMLInputElement &&
            (input.type === "radio" || input.type === "checkbox")) {
            input.checked = false;
        } else {
            input.value = "";
        }
    });
}

function updateSingleAiToolState() {
    updateSingleAiToolMode();
    updateActivityToolVisibility();
}

singleAiToolCheckbox?.addEventListener("change", () => {
    if (!singleAiToolCheckbox.checked) {
        updateSingleAiToolState();
        return;
    }

    if (getRegisteredActivityCount() === 0) {
        updateSingleAiToolState();
        return;
    }

    updateSingleAiToolWarning();
    singleAiToolCheckbox.checked = false;
    singleAiToolDialog?.showModal();
});

keepSingleAiToolButton?.addEventListener("click", () => {
    singleAiToolDialog?.close();
    singleAiToolCheckbox.checked = false;
});

removeSingleAiToolButton?.addEventListener("click", () => {
    clearAllAiData();
    singleAiToolCheckbox.checked = true;
    singleAiToolDialog?.close();
    updateSingleAiToolState();
});

singleAiToolDialog?.addEventListener("cancel", () => {
    singleAiToolCheckbox.checked = false;
});

updateSingleAiToolMode();

restoreSelectedActivityTables();

document.querySelectorAll(".add-custom-activity").forEach((button) => {
    button.addEventListener("click", () => {
        const phaseId = button.dataset.phaseId;
        const list = document.querySelector(
            `.custom-activity-list[data-phase-id="${phaseId}"]`
        );
        const template = document.querySelector(
            `.custom-activity-template[data-phase-id="${phaseId}"]`
        );
        const totalForms = document.getElementById(
            `id_custom_phase_${phaseId}-TOTAL_FORMS`
        );

        if (!list || !template || !totalForms) {
            return;
        }

        const formIndex = Number(totalForms.value);
        const newActivity = document.createElement("div");
        newActivity.innerHTML = template.innerHTML.replaceAll(
            "__prefix__",
            formIndex
        );
        const activity = newActivity.firstElementChild;

        list.appendChild(activity);
        totalForms.value = formIndex + 1;

        const activityName = activity.querySelector(
            "input[name$='activity_name']"
        );
        const activityCheckbox = activity.querySelector(".activity-checkbox");
        const activityFields = activity.querySelector(".activity-fields");
        const processInputs = activityFields.querySelectorAll(
            "input, textarea"
        );
        bindActivityCheckbox(
            activityCheckbox,
            activityFields
        );
        updatePhaseActivityCounter(list.closest(".card"));

        processInputs.forEach((input) => {
            input.disabled = true;
        });
        activity.open = true;
        showActivityFields(activityCheckbox);
        activityName.addEventListener("input", () => {
            const nameLabel = activity.querySelector(".custom-activity-name");
            if (nameLabel) {
                nameLabel.textContent = activityName.value.trim()
                    || "";
            }
        });
        updateActivityToolVisibility();
        activityName.focus();
    });
});

document.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof Element)) {
        return;
    }

    const removeButton = target.closest(".remove-custom-activity");
    if (!removeButton) {
        return;
    }

    event.preventDefault();
    event.stopPropagation();

    const activity = removeButton.closest(".custom-activity-card");
    const list = removeButton.closest(".custom-activity-list");
    if (!activity || !list) {
        return;
    }

    removeCustomActivityCard(activity, list);
});

function removeCustomActivityCard(activity, list) {
    const totalForms = document.getElementById(
        `id_custom_phase_${list.dataset.phaseId}-TOTAL_FORMS`
    );
    if (!totalForms) {
        return;
    }

    activity.remove();
    updatePhaseActivityCounter(list.closest(".card"));
    const activities = [...list.querySelectorAll(".custom-activity-card")];
    activities.forEach((currentActivity, index) => {
        const currentName = currentActivity.querySelector(
            "input[name$='activity_name']"
        );
        if (!currentName) {
            return;
        }

        const currentIndexMatch = currentName.name.match(/-(\d+)-activity_name$/);
        if (!currentIndexMatch) {
            return;
        }

        const currentIndex = currentIndexMatch[1];
        currentActivity
            .querySelectorAll("[name], [id], [for], [data-fields-id]")
            .forEach((element) => {
                ["name", "id", "for", "data-fields-id"].forEach((attribute) => {
                    const value = element.getAttribute(attribute);
                    if (value) {
                        element.setAttribute(
                            attribute,
                            value
                                .replace(`-${currentIndex}-`, `-${index}-`)
                                .replace(`_${currentIndex}`, `_${index}`)
                        );
                    }
                });
            });

        const checkbox = currentActivity.querySelector(".activity-checkbox");
        if (checkbox) {
            checkbox.value = checkbox.value.replace(
                `-${currentIndex}`,
                `-${index}`
            );
        }
    });
    totalForms.value = activities.length;
}

restoreSelectedActivityTables();

function toggleActivityFields(activity) {
    const checkbox = activity.querySelector(".activity-checkbox");
    const fields = activity.querySelector(".activity-fields");

    fields.hidden = !checkbox.checked;
    fields.querySelectorAll("input, textarea").forEach((input) => {
        input.disabled = !checkbox.checked;
    });
}

// Result
const copyDeclarationButton = document.getElementById("copy-declaration");
if (copyDeclarationButton) {
    copyDeclarationButton.addEventListener("click", async () => {
        const text = document.getElementById("declaration").innerText;
        try {
            await navigator.clipboard.writeText(text);
            alert("Declaración copiada correctamente.");
        } catch {
            alert("No se pudo copiar. Selecciona el texto y cópialo manualmente.");
        }
    });
}

function getRegisteredActivityCount() {
    return document.querySelectorAll(
        "form .selected-activities-table tbody tr[data-activity-key]"
    ).length;
}

function updateSingleAiToolWarning() {
    const count = getRegisteredActivityCount();
    const message = singleAiToolDialog?.querySelector("p");

    if (message) {
        message.textContent =
            `Hay ${count} actividad${count === 1 ? "" : "es"} registrada${count === 1 ? "" : "s"}. ` +
            "Si marcas esta opción se eliminarán todos los datos registrados.";
    }
}