"""
Demonstration of Complex Elements Feature
Shows how mandatory vs optional complex elements work in the EIT Tool.
"""

from core.xsd_parser import XSDParser
from core.data_model import DataModelGenerator
from core.complex_form_generator import ComplexFormGenerator


def demo_complex_elements():
    print("🎯 EIT Tool - Complex Elements Demo")
    print("=" * 60)
    
    # Parse XSD
    parser = XSDParser('EIT IT Tool - Extended_projects_v1.16.xsd')
    parsed_data = parser.parse()
    print(f"✅ Loaded XSD: {parsed_data['root_element']}")
    
    # Analyze structure
    complex_elements = parser.get_complex_elements()
    simple_elements = parser.get_simple_elements()
    
    print(f"\n📊 Structure Analysis:")
    print(f"  Total elements: {len(complex_elements) + len(simple_elements)}")
    print(f"  Complex elements (containers): {len(complex_elements)}")
    print(f"  Simple elements (data holders): {len(simple_elements)}")
    
    # Categorize complex elements
    required_complex = [elem for elem in complex_elements if elem.required]
    optional_complex = [elem for elem in complex_elements if not elem.required]
    
    print(f"\n📦 Complex Elements Breakdown:")
    print(f"  ✅ Required (always shown): {len(required_complex)}")
    print(f"  🔄 Optional (user choice): {len(optional_complex)}")
    
    print(f"\n📋 Required Complex Elements (Mandatory Sections):")
    for i, elem in enumerate(required_complex[:10], 1):
        children_count = len(elem.children) if elem.children else 0
        print(f"  {i:2d}. {elem.name:<25} ({children_count:2d} children)")
    
    if len(required_complex) > 10:
        print(f"      ... and {len(required_complex) - 10} more required elements")
    
    print(f"\n🔄 Optional Complex Elements (User Can Include/Exclude):")
    for i, elem in enumerate(optional_complex, 1):
        children_count = len(elem.children) if elem.children else 0
        print(f"  {i:2d}. {elem.name:<25} ({children_count:2d} children)")
        if elem.documentation:
            print(f"      Description: {elem.documentation}")
    
    # Show some examples of hierarchical structure
    print(f"\n🌳 Hierarchical Structure Examples:")
    
    # Find some interesting examples
    examples = ['Outputs', 'ProjectPlannedBudget', 'FinancialSustainability']
    
    for example_name in examples:
        for elem in complex_elements:
            if elem.name == example_name:
                required_status = "REQUIRED" if elem.required else "OPTIONAL"
                print(f"\n  📦 {elem.name} ({required_status}):")
                if elem.documentation:
                    print(f"     Description: {elem.documentation}")
                
                if elem.children:
                    print(f"     Children ({len(elem.children)}):")
                    for child in elem.children:
                        child_type = "📦 Complex" if child.is_complex else "📝 Simple"
                        child_req = "Required" if child.required else "Optional"
                        print(f"       - {child.name} ({child_type}, {child_req})")
                        
                        # Show grandchildren for complex children
                        if child.is_complex and child.children:
                            print(f"         Grandchildren ({len(child.children)}):")
                            for grandchild in child.children[:3]:
                                gc_req = "Required" if grandchild.required else "Optional"
                                print(f"           • {grandchild.name} ({gc_req})")
                            if len(child.children) > 3:
                                print(f"           • ... and {len(child.children) - 3} more")
                break
    
    print(f"\n🎯 How This Works in the Form:")
    print(f"  1. ✅ Required complex elements → Always shown with all their children")
    print(f"  2. 🔄 Optional complex elements → Show checkbox to include/exclude")
    print(f"  3. 👁️ When optional element is excluded → All its children are hidden")
    print(f"  4. 👁️ When optional element is included → All its children appear")
    print(f"  5. 🌳 Nested structure → Maintains XML hierarchy in the form")
    
    print(f"\n🚀 To use this feature:")
    print(f"  1. Run: streamlit run app.py")
    print(f"  2. Load the XSD schema")
    print(f"  3. Choose 'Hierarchical Form (Complex Elements)' in Data Entry tab")
    print(f"  4. See optional sections with checkboxes to include/exclude")
    
    print(f"\n🎉 Complex Elements Demo Complete!")


if __name__ == "__main__":
    demo_complex_elements()