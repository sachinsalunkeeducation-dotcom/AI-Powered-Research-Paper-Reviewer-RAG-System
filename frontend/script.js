const pdfFile = document.getElementById("pdfFile");
const fileName = document.getElementById("fileName");
const uploadBtn = document.getElementById("uploadBtn");
const status = document.getElementById("status");

const result = document.getElementById("result");

const pageCount = document.getElementById("pageCount");
const chunkCount = document.getElementById("chunkCount");
const embeddingShape = document.getElementById("embeddingShape");


pdfFile.addEventListener("change", () => {

    if (pdfFile.files.length > 0) {

        fileName.textContent =
            pdfFile.files[0].name;

        status.textContent = "";

    }

});


uploadBtn.addEventListener("click", async () => {

    if (pdfFile.files.length === 0) {

        status.textContent =
            "Please select a PDF first.";

        return;

    }


    const file = pdfFile.files[0];


    const formData = new FormData();

    formData.append(
        "file",
        file
    );


    uploadBtn.disabled = true;

    status.textContent =
        "Processing paper...";


    try {

        const response = await fetch(
            "http://127.0.0.1:8000/papers/upload",
            {
                method: "POST",
                body: formData
            }
        );


        console.log(
            "HTTP status:",
            response.status
        );


        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Backend response:",
            data
        );


        // Update page count
        pageCount.textContent =
            data.pages ?? 0;


        // Update chunk count
        chunkCount.textContent =
            data.chunks ?? 0;


        // Update embedding shape
        if (
            data.embedding_shape &&
            Array.isArray(data.embedding_shape)
        ) {

            embeddingShape.textContent =
                data.embedding_shape.join(" × ");

        } else {

            embeddingShape.textContent =
                "N/A";

        }


        // Show result card
        result.classList.remove(
            "hidden"
        );


        status.textContent =
            "Paper processed successfully!";


    } catch (error) {

        console.error(
            "Upload error:",
            error
        );


        status.textContent =
            "Error: " + error.message;

    }


    uploadBtn.disabled = false;

});