// Load servers from the server and populate the table
async function loadServers() {
    const serverList = document.getElementById('server-list');
    if (!serverList) {
        console.error("Error: Element with ID 'server-list' not found.");
        return;
    }
    serverList.innerHTML = ''; // Clear existing rows

    try {
        const response = await fetch('/list');
        if (!response.ok) {
            throw new Error("Server error.");
        }

        const servers = await response.json();
        servers.forEach((server, index) => {
            const row = serverList.insertRow();

            // R.No.
            row.insertCell().textContent = index + 1;

            // Server IP
            row.insertCell().textContent = server.ip;

            // Port Number
            row.insertCell().textContent = server.port;

            // Server Name
            row.insertCell().textContent = server.name;

            // Ping Button
            const pingCell = row.insertCell();
            const pingButton = document.createElement('button');
            pingButton.textContent = 'Ping';
            pingButton.classList.add('ping-button');
            pingButton.onclick = () => testPing(server.ip);
            pingCell.appendChild(pingButton);

            // Telnet Button
            const telnetCell = row.insertCell();
            const telnetButton = document.createElement('button');
            telnetButton.textContent = 'Telnet';
            telnetButton.classList.add('telnet-button');
            telnetButton.onclick = () => testTelnet(server.ip, server.port);
            telnetCell.appendChild(telnetButton);

            // Edit Button
            const editCell = row.insertCell();
            const editButton = document.createElement('button');
            editButton.textContent = 'Edit';
            editButton.classList.add('edit-button');
            editButton.onclick = () => openEditModal(server);
            editCell.appendChild(editButton);

            // Delete Button
            const deleteCell = row.insertCell();
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'Delete';
            deleteButton.classList.add('delete-button');
            deleteButton.onclick = () => confirmDelete(server.id);
            deleteCell.appendChild(deleteButton);
        });
    } catch (error) {
        console.error('Error loading servers:', error);
        serverList.innerHTML = `<tr><td colspan='8'>${error.message}</td></tr>`;
    }
}

// Test Ping with Loading Indicator
function testPing(ip) {
    if (!ip) {
        alert("Invalid IP address.");
        return;
    }

    const errorMessageDiv = document.getElementById('error-message');
    errorMessageDiv.style.display = 'block'; // Show loading message
    errorMessageDiv.textContent = "Loading... Please wait."; // Set loading text

    // Fetch ping result
    fetch(`/ping/${ip}`, { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            errorMessageDiv.style.display = 'none'; // Hide loading message
            if (data.error) {
                alert(`Ping Error: ${data.error}`); // Show error in popup
            } else {
                alert(`Ping Successful:\n\n${data.output}`); // Show success in popup
            }
        })
        .catch(error => {
            errorMessageDiv.style.display = 'none'; // Hide loading message on failure
            console.error("Error during ping:", error);
            alert("An unexpected error occurred during the ping operation."); // Show generic error in popup
        });
}

// Test Telnet with Loading Indicator
function testTelnet(ip, port) {
    if (!ip || !port) {
        alert("Invalid IP or port.");
        return;
    }

    const errorMessageDiv = document.getElementById('error-message');
    errorMessageDiv.style.display = 'block'; // Show loading message
    errorMessageDiv.textContent = "Loading... Please wait."; // Set loading text

    // Fetch telnet result
    fetch(`/telnet/${ip}/${port}`, { method: 'GET' })
        .then(response => response.json())
        .then(data => {
            errorMessageDiv.style.display = 'none'; // Hide loading message
            if (data.error) {
                alert(`Telnet Error: ${data.error}`); // Show error in popup
            } else {
                alert(data.message); // Show success in popup
            }
        })
        .catch(error => {
            errorMessageDiv.style.display = 'none'; // Hide loading message on failure
            console.error("Error during telnet:", error);
            alert("An unexpected error occurred during the telnet operation."); // Show generic error in popup
        });
}

// Open the edit modal with pre-filled data
function openEditModal(server) {
    document.getElementById('edit-server-id').value = server.id;
    document.getElementById('edit-server-ip').value = server.ip;
    document.getElementById('edit-server-port').value = server.port;
    document.getElementById('edit-server-name').value = server.name;
    document.getElementById('edit-modal').style.display = 'block';
}

// Close the edit modal
function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

// Update server function
async function updateServer() {
    const id = document.getElementById('edit-server-id').value;
    const ip = document.getElementById('edit-server-ip').value.trim();
    const port = parseInt(document.getElementById('edit-server-port').value.trim(), 10);
    const name = document.getElementById('edit-server-name').value.trim();

    if (!ip || !name || !port) {
        alert("Please fill out all fields.");
        return;
    }

    try {
        const response = await fetch(`/update/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, name, port })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to update server.");
        }

        closeEditModal(); // Close the modal after successful update
        loadServers(); // Reload the server list
    } catch (error) {
        console.error("Error updating server:", error);
        alert(error.message);
    }
}

// Confirm deletion of a server
function confirmDelete(id) {
    if (confirm("Are you sure you want to delete this server?")) {
        deleteServer(id);
    }
}

// Delete server function
async function deleteServer(id) {
    try {
        const response = await fetch(`/delete/${id}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to delete server.");
        }

        loadServers(); // Reload the server list after deletion
    } catch (error) {
        console.error("Error deleting server:", error);
        alert(error.message);
    }
}

// Submit new server function
async function submitServer() {
    const ip = document.getElementById('server-ip').value.trim();
    const port = parseInt(document.getElementById('server-port').value.trim(), 10);
    const name = document.getElementById('server-name').value.trim();

    if (!ip || !name || !port) {
        alert("Please fill out all fields.");
        return;
    }

    try {
        const response = await fetch('/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ip, name, port })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || "Failed to add server.");
        }

        document.getElementById('server-ip').value = '';
        document.getElementById('server-port').value = '';
        document.getElementById('server-name').value = '';
        loadServers(); // Reload the server list after adding
    } catch (error) {
        console.error("Error adding server:", error);
        alert(error.message);
    }
}

// Ensure the script runs when the page loads
document.addEventListener("DOMContentLoaded", () => {
    loadServers();
});

// Filter table functionality for guest/admin view
function filterTable() {
    const input = document.getElementById('search-bar').value.toLowerCase(); // Get search input
    const rows = document.querySelectorAll('#server-list tr'); // Select all rows in the table

    // Iterate through each row and hide/show based on search input
    rows.forEach(row => {
        const ipCell = row.cells[1]?.textContent?.toLowerCase() || ''; // Server IP (column 2)
        const portCell = row.cells[2]?.textContent?.toLowerCase() || ''; // Port Number (column 3)
        const nameCell = row.cells[3]?.textContent?.toLowerCase() || ''; // Server Name (column 4)

        // Check if any cell matches the search input
        if (ipCell.includes(input) || nameCell.includes(input) || portCell.includes(input)) {
            row.style.display = ''; // Show the row
        } else {
            row.style.display = 'none'; // Hide the row
        }
    });
}