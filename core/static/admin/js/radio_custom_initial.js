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

document.addEventListener('DOMContentLoaded', function () {
	const searchContainer = document.createElement('div');
	searchContainer.innerHTML = `<input type="text" id="list-search" placeholder="Filter" style="margin-bottom: 10px;">`;
	const userList = document.querySelector('.searchable');
	userList.before(searchContainer);

	const userSearch = document.getElementById('list-search');
	userSearch.addEventListener('keyup', function () {
		const searchTerm = userSearch.value.toLowerCase();
		const options = userList.options;

		for (let opt of options) {
			const userName = opt.text.toLowerCase();
			const userEmail = opt.value.toLowerCase();
			if (userName.includes(searchTerm) || userEmail.includes(searchTerm)) {
				opt.style.display = 'block';
			} else {
				opt.style.display = 'none';
			}
		}
	});
});
