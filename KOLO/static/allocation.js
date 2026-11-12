// chatgpt was used to assist in developing the allocation.js code
// Get all the percentage inputs
const inputs = document.querySelectorAll(".allocation-input");

// Get the elements that display the total and message
const totalDisplay = document.querySelector("#total-percentage");
const message = document.querySelector("#allocation-message");

// Function to calculate the total
function calculateTotal() {
    let total = 0;

    // Add all the percentage values
    inputs.forEach(input => {
        total += Number(input.value) || 0;
    });

    // Display the total
    totalDisplay.textContent = Math.round(total) + "%";

    // Check whether the total is 100%
    if (Math.abs(total - 100) < 0.01) {
        message.textContent = "Your allocations add up correctly!";
    } else {
        message.textContent = "Your allocations must add up to 100%.";
    }
}

// Listen for changes in each input
inputs.forEach(input => {
    input.addEventListener("input", calculateTotal);
});

// Calculate the initial total when the page loads
calculateTotal();

inputs.forEach(input => {
    input.addEventListener("change", function() {
        this.value = Math.round(Number(this.value));
        calculateTotal();
    });
});