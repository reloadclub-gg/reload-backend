window.onload = () => {
	const url = window.location.href;
	const activeInputs = document.querySelectorAll('input[name="user_filter"]');
	const radios = document.querySelector(".form-check-inline");
	const radiosChildren = radios.children;

	radios.style.display = "flex";
	radiosChildren[0].style.display = "flex";
	radiosChildren[1].style.display = "flex";

	radiosChildren[0].children[0].style.display = "flex";
	radiosChildren[0].children[0].style.alignItems = "center";
	radiosChildren[0].children[0].style.gap = "5px";

	radiosChildren[1].children[0].style.display = "flex";
	radiosChildren[1].children[0].style.alignItems = "center";
	radiosChildren[1].children[0].style.gap = "5px";

	if (url.includes("?")) {
		activeInputs[1].setAttribute("checked", "");
	} else {
		activeInputs[0].setAttribute("checked", "");
	}
};
