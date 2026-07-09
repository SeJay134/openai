/* =========================
   DOM ELEMENTS
========================= */

const welcomeText =
  document.getElementById("app_welcome"); // welcomeText

const chatInput =
  document.getElementById("input"); // chatInput

/* =========================
   text welcome
========================= */

const titleText =
  "Hello! I’m Sergei’s portfolio assistant. I use an LLM enhanced with Retrieval‑Augmented Generation to provide reliable, context‑aware answers about my work and experience." 
// const titleText =
//   "Hi, I'm Sergei — a programmer and software developer. This project is both my portfolio and personal AI assistant, created to showcase my skills and help with everyday tasks. Feel free to ask anything — it will do its best to assist you. Enjoy exploring!";

/* in to div */

app_welcome.textContent =
  titleText;

/* =========================
   smooth show
========================= */

window.addEventListener("load", () => {

  setTimeout(() => {

    app_welcome.classList.add("show");

  }, 200);

});

/* =========================
   disappear on focus
========================= */

input.addEventListener("focus", () => {

  app_welcome.classList.remove("show");

  app_welcome.classList.add("hide");

});