document.querySelector("form").addEventListener("submit", e => {
  if (document.querySelector("#password").value
    === document.querySelector("#confirm-password").value) {
    document.querySelector("form").submit();
  } else {
    document.querySelector("#error").innerHTML =
      "<div>Passwords do not match.</div>";
    e.preventDefault();
  }
});
