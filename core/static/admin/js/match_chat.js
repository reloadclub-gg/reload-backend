document.addEventListener('DOMContentLoaded', (event) => {
	const chatBox = document.querySelector("#chatBox");
	const usernameSearch = document.querySelector("#usernameSearch");
	const steamidSearch = document.querySelector("#steamidSearch");
	const messageSearch = document.querySelector("#messageSearch");

	const displayMessages = (messages) => {
			chatBox.innerHTML = '';
			messages.forEach((message) => {
					const messageElement = document.createElement("div");
					messageElement.classList.add("message");

					const usernameLink = document.createElement("a");
					usernameLink.href = `/admin/accounts/user/${message.user_id}/change/`;
					usernameLink.textContent = message.username;
					usernameLink.classList.add("username");

					const targetSpan = document.createElement("span");
					targetSpan.textContent = ` [${message.target}]: `;
					targetSpan.classList.add("target");
					targetSpan.classList.add(message.target);

					const messageSpan = document.createElement("span");
					messageSpan.textContent = ` ${message.message} `;
					messageSpan.classList.add("message-content");

					const dateSpan = document.createElement("span");
					dateSpan.textContent = `(${message.date})`;
					dateSpan.classList.add("date");

					messageElement.append(usernameLink, targetSpan, messageSpan, dateSpan);

					chatBox.append(messageElement);
			});
	};

	const filterMessages = () => {
			const usernameText = usernameSearch.value.toLowerCase();
			const steamidText = steamidSearch.value.toLowerCase();
			const messageText = messageSearch.value.toLowerCase();

			const filteredMessages = chatData.filter(message =>
					(usernameText.length < 3 || message.username.toLowerCase().includes(usernameText)) &&
					(steamidText.length < 3 || message.steamid.toLowerCase().includes(steamidText)) &&
					(messageText.length < 3 || message.message.toLowerCase().includes(messageText))
			);
			displayMessages(filteredMessages);
	};

	if (typeof chatData !== 'undefined') {
			chatData.sort((a, b) => new Date(a.date) - new Date(b.date));
			displayMessages(chatData);

			usernameSearch.addEventListener('input', filterMessages);
			steamidSearch.addEventListener('input', filterMessages);
			messageSearch.addEventListener('input', filterMessages);
	}
});
