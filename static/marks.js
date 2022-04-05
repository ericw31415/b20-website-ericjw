(function() {
  const modified = new Set();

  function edit() {
    document.querySelector("#edit").style.display = "none";
    document.querySelector("#save").style.display = "inline-block";
    document.querySelector("#cancel").style.display = "inline-block";

    document.querySelectorAll(".tr:not(.th) > .td:nth-child(3)").forEach(e => {
      const value = e.innerHTML.trim();
      const newInput = document.createElement("input");
      newInput.type = "number";
      newInput.value = value === "\u2014" ? "" : value;
      newInput.addEventListener("change", e => {
        modified.add(newInput.parentElement.parentElement);
      });
      e.innerHTML = "";
      e.appendChild(newInput);
    });
  }

  function save() {
    const marks = {};
    for (const row of modified) {
      marks[row.firstElementChild.innerHTML] =
        row.lastElementChild.firstElementChild.value;
    }
    document.querySelector("#data").value = JSON.stringify(marks);
    document.querySelector(".dummy-form").submit()
  }

  document.querySelector("#edit").addEventListener("click", edit);
  document.querySelector("#save").addEventListener("click", save);
  document.querySelector("#cancel").addEventListener("click", e => {
    window.location.reload();
  });
})();
