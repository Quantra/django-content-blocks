// Show or hide the loader.
// todo Control the delayed fade in of the inner loader with CSS.

const loader = document.getElementById("loader");

function showLoader() {
  loader.classList.remove("hidden");
}

function hideLoader() {
  loader.classList.add("hidden");
}
