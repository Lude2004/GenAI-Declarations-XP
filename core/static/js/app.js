// Form
const activityCheckboxes = document.querySelectorAll(".activity-checkbox");
const singleAiToolCheckbox = document.getElementById("id_use_single_ai_tool");
const globalAiTool = document.querySelector(".global-ai-tool");

function updateSingleAiToolMode() {
    const enabled = singleAiToolCheckbox?.checked ?? false;
    if (globalAiTool) {
        globalAiTool.hidden = !enabled;
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

    if (globalAiTool) {
        globalAiTool.querySelectorAll("input, textarea, select").forEach((input) => {
            input.disabled = !enabled;
        });
    }
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

    checkbox.addEventListener("change", () => {
        activityFields.hidden = !checkbox.checked;
        inputs.forEach((input) => {
            input.disabled = !checkbox.checked;
            if (!checkbox.checked) {
                input.value = "";
            }
        });
        updateActivityToolVisibility();
    });
});

singleAiToolCheckbox?.addEventListener("change", updateSingleAiToolMode);
updateSingleAiToolMode();

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
        const activityFields = activity.querySelector(".activity-fields");
        const processInputs = activityFields.querySelectorAll(
            "input, textarea"
        );

        processInputs.forEach((input) => {
            input.disabled = true;
        });
        activityName.addEventListener("input", () => {
            const hasName = activityName.value.trim().length > 0;
            activityFields.hidden = !hasName;
            processInputs.forEach((input) => {
                input.disabled = !hasName;
            });
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

    const totalForms = document.getElementById(
        `id_custom_phase_${list.dataset.phaseId}-TOTAL_FORMS`
    );
    if (!totalForms) {
        return;
    }

    activity.remove();
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
});

function toggleActivityFields(activity) {
    const checkbox = activity.querySelector(".activity-checkbox");
    const fields = activity.querySelector(".activity-fields");

    fields.hidden = !checkbox.checked;
    fields.querySelectorAll("input, textarea").forEach((input) => {
        input.disabled = !checkbox.checked;
    });
}