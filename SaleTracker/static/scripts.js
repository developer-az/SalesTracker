function scrollToContent() {
  const contentElement = document.querySelector("#content");
  contentElement.scrollIntoView({ behavior: "smooth" });
}

let mybutton = document.getElementById("myBtn");

window.onscroll = function () {
  scrollFunction();
};

function scrollFunction() {
  if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    mybutton.style.display = "block";
  } else {
    mybutton.style.display = "none";
  }
}

function topFunction() {
  document.body.scrollTo({ top: 0, behavior: "smooth" });
  document.documentElement.scrollTo({ top: 0, behavior: "smooth" });
}

document
  .getElementById("combinedForm")
  .addEventListener("submit", function (event) {
    event.preventDefault();

    const recipient_email = document.getElementById("email").value;
    const productLink = document.getElementById("productLink").value;

    fetch("http://127.0.0.1:5000/update-product-link", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ productLink: productLink }),
    })
      .then((response) => {
        if (response.ok) {
          console.log("Product link updated successfully!");
          return fetch("http://127.0.0.1:5000/schedule-email", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ recipient_email: recipient_email }),
          });
        } else {
          throw new Error("Error updating product link");
        }
      })
      .then((response) => {
        if (response.ok) {
          alert("Email sent successfully!");
        } else {
          alert("Error sending email!");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        alert(`Error: ${error.message}`);
      });
  });
