from fpdf import FPDF
from pathlib import Path
from app.agents.planner_agent import Plan

class PlanPDF(FPDF):
    def header(self):
        # Top banner styling
        self.set_fill_color(30, 41, 59) # Slate 800 (navy dark slate)
        self.rect(0, 0, 210, 25, "F")
        
        self.set_y(8)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "REPOFIX AGENT - IMPLEMENTATION PLAN", align="C", ln=1)
        
        self.set_y(28) # Reset cursor position below header

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(148, 163, 184) # Slate 400
        # Line above footer
        self.set_draw_color(226, 232, 240) # Slate 200
        self.line(10, 282, 200, 282)
        # Page number
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")

def generate_plan_pdf(plan: Plan, repo_url: str, issue_desc: str, cloned_path: str, output_path: str):
    # Setup document
    pdf = PlanPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_margins(15, 30, 15)
    pdf.add_page()
    
    # Metadata Box
    pdf.set_fill_color(248, 250, 252) # Slate 50
    pdf.set_draw_color(226, 232, 240) # Slate 200
    pdf.rect(15, 32, 180, 42, "FD")
    
    # Write metadata contents
    pdf.set_xy(18, 35)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(71, 85, 105) # Slate 600
    pdf.cell(35, 6, "Repository URL:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 41, 59) # Slate 800
    pdf.cell(0, 6, repo_url, ln=1)
    
    pdf.set_x(18)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(35, 6, "Issue Summary:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(30, 41, 59)
    # Truncate issue description if it is too long for the summary card
    summary_desc = issue_desc.strip().replace("\n", " ")
    if len(summary_desc) > 85:
        summary_desc = summary_desc[:85] + "..."
    pdf.cell(0, 6, summary_desc, ln=1)
    
    pdf.set_x(18)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(35, 6, "Cloned Path:")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 116, 139) # Slate 500
    pdf.cell(0, 6, str(cloned_path), ln=1)
    
    # 1. Overview
    pdf.set_xy(15, 80)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 23, 42) # Slate 900
    pdf.cell(0, 8, "1. Overview & Objectives", ln=1)
    pdf.ln(1)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85) # Slate 700
    pdf.multi_cell(180, 5, plan.overview)
    pdf.ln(6)
    
    # 2. Proposed File Changes
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "2. Proposed File Changes", ln=1)
    pdf.ln(2)
    
    if not plan.changes:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(0, 6, "No direct file changes planned.", ln=1)
    else:
        for change in plan.changes:
            # Check page break space
            if pdf.get_y() > 240:
                pdf.add_page()
                pdf.ln(5)
                
            pdf.set_font("Helvetica", "B", 10)
            change_type = change.model # "Modify", "New", "Delete"
            
            # Badge drawing
            if change_type == "New":
                pdf.set_fill_color(220, 252, 231) # Green 100
                pdf.set_text_color(21, 128, 61) # Green 700
            elif change_type == "Delete":
                pdf.set_fill_color(254, 226, 226) # Red 100
                pdf.set_text_color(185, 28, 28) # Red 700
            else:
                pdf.set_fill_color(219, 234, 254) # Blue 100
                pdf.set_text_color(29, 78, 216) # Blue 700
                
            # Draw badge
            pdf.cell(22, 6, f" {change_type.upper()} ", ln=0, fill=True, align="C")
            
            # File path next to badge
            pdf.set_text_color(15, 23, 42)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(5, 6, "") # spacer
            pdf.cell(0, 6, str(change.file_path), ln=1)
            
            # Description
            pdf.set_font("Helvetica", "", 9.5)
            pdf.set_text_color(71, 85, 105)
            pdf.set_x(42) # Align with the path start
            pdf.multi_cell(153, 4.5, change.description)
            pdf.ln(4)
            
    pdf.ln(4)
    
    # 3. Checklist / Tasks
    if pdf.get_y() > 220:
        pdf.add_page()
        pdf.ln(5)
        
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "3. Step-by-Step Task Checklist", ln=1)
    pdf.ln(2)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    for task in plan.task:
        if pdf.get_y() > 260:
            pdf.add_page()
            pdf.ln(5)
            
        # Draw a custom checkbox [  ]
        pdf.set_font("Courier", "B", 12)
        pdf.set_text_color(71, 85, 105)
        pdf.cell(10, 6, "[ ]")
        
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(51, 65, 85)
        pdf.multi_cell(170, 6, task)
        pdf.ln(1)
        
    pdf.ln(6)
    
    # 4. Verification / Testing
    if pdf.get_y() > 220:
        pdf.add_page()
        pdf.ln(5)
        
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "4. Verification & Testing Instructions", ln=1)
    pdf.ln(1)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    pdf.multi_cell(180, 5, plan.tests)
    
    # Write to file
    pdf.output(output_path)
