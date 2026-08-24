
import gradio as gr

students = ["Arun", "Bala", "Kumar", "Priya", "Divya"]

def save_marks(class_name, subject, exam, *marks):
    result = f"## Marks Saved\n\n"
    result += f"**Class:** {class_name}  \n"
    result += f"**Subject:** {subject}  \n"
    result += f"**Exam:** {exam}\n\n"

    result += "| Student Name | Mark |\n"
    result += "|---|---:|\n"

    for student, mark in zip(students, marks):
        result += f"| {student} | {mark} |\n"

    return result


with gr.Blocks() as app:

    gr.Markdown("# 📝 School Mark Entry")

    with gr.Row():
        class_name = gr.Dropdown(
            ["10-A"],
            label="Class",
            value="10-A"
        )

        subject = gr.Dropdown(
            ["Computer Science"],
            label="Subject",
            value="Computer Science"
        )

        exam = gr.Dropdown(
            ["Unit Test", "Quarterly", "Half-Yearly", "Annual"],
            label="Exam",
            value="Quarterly"
        )

    gr.Markdown("### Student Marks")

    mark_boxes = []

    for student in students:
        with gr.Row():
            gr.Markdown(student)
            mark_box = gr.Number(
                label="Mark",
                minimum=0,
                maximum=100
            )
            mark_boxes.append(mark_box)

    save_button = gr.Button("💾 SAVE MARKS")

    result = gr.Markdown()

    save_button.click(
        save_marks,
        inputs=[class_name, subject, exam] + mark_boxes,
        outputs=result
    )

app.launch()
