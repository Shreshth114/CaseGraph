/* Shared listbox for native selects that need styled, keyboard-operable menus. */
const selectMenu = document.createElement("div");
selectMenu.id = "select-options";
selectMenu.className = "select-menu";
selectMenu.setAttribute("role", "listbox");
selectMenu.hidden = true;
document.body.append(selectMenu);

let openSelect = null;
let activeOption = -1;
let typed = "";
let typeTime = 0;

function positionSelectMenu() {
  if (!openSelect) return;
  if (!openSelect.trigger.isConnected) {
    closeSelectMenu();
    return;
  }
  const rect = openSelect.trigger.getBoundingClientRect();
  if (rect.bottom < 0 || rect.top > window.innerHeight) {
    closeSelectMenu();
    return;
  }
  const margin = 8;
  const width = Math.min(Math.max(rect.width, 192), window.innerWidth - 2 * margin);
  const below = window.innerHeight - rect.bottom - 2 * margin;
  const above = rect.top - 2 * margin;
  const flip = below < Math.min(240, selectMenu.scrollHeight) && above > below;
  selectMenu.style.width = width + "px";
  selectMenu.style.left = Math.max(margin, Math.min(rect.left, window.innerWidth - width - margin)) + "px";
  selectMenu.style.maxHeight = Math.min(288, Math.max(0, flip ? above : below)) + "px";
  selectMenu.style.top = (flip ? rect.top - selectMenu.offsetHeight - margin : rect.bottom + margin) + "px";
  selectMenu.classList.toggle("opens-up", flip);
}

function closeSelectMenu() {
  if (!openSelect) return;
  openSelect.trigger.setAttribute("aria-expanded", "false");
  openSelect.trigger.removeAttribute("aria-activedescendant");
  selectMenu.hidden = true;
  openSelect = null;
  typed = "";
}

function highlightOption(index) {
  const options = selectMenu.children;
  if (!options.length) return;
  activeOption = Math.max(0, Math.min(index, options.length - 1));
  for (const row of options) row.classList.toggle("highlighted", row === options[activeOption]);
  openSelect.trigger.setAttribute("aria-activedescendant", options[activeOption].id);
  const option = options[activeOption];
  if (option.offsetTop < selectMenu.scrollTop) selectMenu.scrollTop = option.offsetTop;
  if (option.offsetTop + option.offsetHeight > selectMenu.scrollTop + selectMenu.clientHeight) {
    selectMenu.scrollTop = option.offsetTop + option.offsetHeight - selectMenu.clientHeight;
  }
}

function chooseOption(index) {
  const { select, trigger, sync } = openSelect;
  const changed = select.selectedIndex !== index;
  select.selectedIndex = index;
  sync();
  closeSelectMenu();
  trigger.focus({ preventScroll: true });
  if (changed) {
    select.dispatchEvent(new Event("input", { bubbles: true }));
    select.dispatchEvent(new Event("change", { bubbles: true }));
  }
}

function showSelectMenu(control) {
  closeSelectMenu();
  openSelect = control;
  selectMenu.setAttribute("aria-labelledby", control.labelId);
  selectMenu.replaceChildren(...Array.from(control.select.options, (option, i) => {
    const row = document.createElement("div");
    row.className = "select-option";
    row.id = "select-option-" + i;
    row.setAttribute("role", "option");
    row.setAttribute("aria-selected", String(option.selected));
    row.textContent = option.text;
    row.addEventListener("click", () => chooseOption(i));
    return row;
  }));
  control.trigger.setAttribute("aria-expanded", "true");
  selectMenu.hidden = false;
  selectMenu.scrollTop = 0;
  positionSelectMenu();
  if (openSelect) highlightOption(control.select.selectedIndex);
}

function styleSelect(select, label) {
  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.id = select.id + "-trigger";
  trigger.className = "select-trigger";
  trigger.setAttribute("role", "combobox");
  trigger.setAttribute("aria-expanded", "false");
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-controls", selectMenu.id);
  label.id ||= select.id + "-label";
  trigger.setAttribute("aria-labelledby", label.id + " " + trigger.id + "-value");
  const value = document.createElement("span");
  value.id = trigger.id + "-value";
  trigger.append(value);
  label.htmlFor = trigger.id;
  select.hidden = true;
  select.after(trigger);
  const sync = () => { value.textContent = select.selectedOptions[0]?.text || ""; };
  const control = { select, trigger, sync, labelId: label.id };
  sync();
  trigger.onclick = () => openSelect === control ? closeSelectMenu() : showSelectMenu(control);
  trigger.onkeydown = event => {
    const visible = openSelect === control;
    const key = event.key;
    if (key === "Tab") {
      if (visible) closeSelectMenu();
      return;
    }
    if (key === "Escape") {
      if (visible) { event.preventDefault(); closeSelectMenu(); }
      return;
    }
    if (event.altKey || event.metaKey || event.ctrlKey) return;
    if (["ArrowDown", "ArrowUp", "Home", "End", "Enter", " "].includes(key)) {
      event.preventDefault();
      if (!visible) showSelectMenu(control);
      if (!openSelect) return;
      if (key === "Home") highlightOption(0);
      if (key === "End") highlightOption(select.options.length - 1);
      if (visible && key === "ArrowDown") highlightOption(activeOption + 1);
      if (visible && key === "ArrowUp") highlightOption(activeOption - 1);
      if (visible && (key === "Enter" || key === " ")) chooseOption(activeOption);
    } else if (key.length === 1) {
      if (!visible) showSelectMenu(control);
      if (!openSelect) return;
      const now = performance.now();
      typed = (now - typeTime < 650 ? typed : "") + key.toLowerCase();
      typeTime = now;
      const index = Array.from(select.options).findIndex(option => option.text.toLowerCase().startsWith(typed));
      if (index >= 0) highlightOption(index);
    }
  };
  return { sync, trigger };
}

document.addEventListener("pointerdown", event => {
  if (openSelect && !openSelect.trigger.contains(event.target) && !selectMenu.contains(event.target)) closeSelectMenu();
});
selectMenu.addEventListener("pointerdown", event => {
  if (event.target.closest(".select-option") && event.pointerType === "mouse") event.preventDefault();
});
window.addEventListener("resize", positionSelectMenu);
window.addEventListener("scroll", event => {
  if (event.target !== selectMenu) positionSelectMenu();
}, true);
