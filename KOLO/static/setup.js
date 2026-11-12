    const savingsOptions = document.querySelectorAll('input[name="savings_choice"]');
    const savingsSection = document.querySelector('#savings_section');
    const savingsAmount = document.querySelector('#savings_amount');

    // Show or hide the savings section based on the selected option
    savingsOptions.forEach(option => {
        option.addEventListener('change', () => {
            if (option.value === "yes") {
                savingsSection.style.display = "block";
                savingsAmount.required = true;
            } else {
                savingsSection.style.display = "none";
                savingsAmount.required = false;
                savingsAmount.value = "";
            }
        })
    });