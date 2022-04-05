function editStatus(username, id, status) {
  document.querySelector("#username").value = username;
  document.querySelector("#ass-id").value = id;
  document.querySelector("#status").value = status;

  document.querySelector(".dummy-form").submit();
}

function accept(username, id) {
  editStatus(username, id, "accepted");
}

function reject(username, id) {
  editStatus(username, id, "rejected");
}
