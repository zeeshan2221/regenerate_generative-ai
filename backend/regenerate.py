import os
from dotenv import load_dotenv
import openai
import plotly.graph_objects as go
import plotly.offline as py
import pydot
import uuid

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


class Regenerate:

    def __init__(self):

        self.prompt_map = {
            "graph": "Represent this information in the form of a list of relationships of all concepts and entities. Capture as many relationships as possible. (Format for relationship: A -> B, Type of Relationship)",
            "timeline": "Represent this information in the form of a list of events in chronological order. (Format for event: Date -> Event)",
        }

    def __call__(self, input_text, plot_type):

        prompt_text = self.create_prompt(input_text, plot_type)
        response_text =  self.call_openai(prompt_text)
        response_dict = self.parse_response_text(response_text, plot_type)
        infographic, infographic_id = self.create_infographic(response_dict, plot_type)

        return {
            "infographic_id": infographic_id,
        }

    def create_prompt(self, input_text, plot_type):

        return input_text + "\n" + self.prompt_map[plot_type]

    def call_openai(self, prompt_text):

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt_text,
            temperature=0,
            max_tokens=512,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            logprobs=3,
        )

        response_text = response["choices"][0]["text"]
        return response_text

    def parse_response_text(self, response_text, plot_type):

        if plot_type == "graph":
            
            graph_dict = {'nodes' : set(), 'edges' : []}
        
            for line_text in response_text.split("\n"):
                
                line_text = line_text.strip("\n")
                if line_text == "":
                    continue

                start_char_idx = 0
                for char in line_text:
                    if char.isalpha():
                        break
                    start_char_idx += 1
                line_text = line_text[start_char_idx:]

                node1_text = line_text.split("->")[0].strip()
                node2_text = line_text.split("->")[1].split(",")[0].strip()
                edge_text = line_text.split("->")[1].split(",")[1].strip()

                graph_dict['nodes'].add(node1_text)
                graph_dict['nodes'].add(node2_text)
                graph_dict['edges'].append((node1_text, node2_text, edge_text))

            return graph_dict

        elif plot_type == "timeline":

            print(response_text)
            
            timeline_dict = {'dates' : [], 'events' : []}
        
            for line_text in response_text.split("\n"):
                
                line_text = line_text.strip("\n")
                if line_text == "":
                    continue
                print(line_text.split("->"))
                date_text = line_text.split("->")[0]
                event_text = line_text.split("->")[1]

                timeline_dict['dates'].append(date_text)
                timeline_dict['events'].append(event_text)

            return timeline_dict

        else:
            raise ValueError("Invalid plot_type")

    def create_infographic(self, response_dict, plot_type):

        infographic_id = str(uuid.uuid4())

        if plot_type == "graph":

            dot_lang_start = """
digraph G {
    ratio=0.75;
    overlap="scalexy";
    graph [dpi=300][bgcolor="#BFD6FF"];
    node [shape=box][fillcolor="#2B3A55"][fontcolor="#ffffff"][style="filled,rounded"][fontname="Helvetica"][fontsize=10];
    edge [fontsize=10][fontname="Helvetica"][color="#CE7777"][fontcolor="#2B3A55"][penwidth=2.0];"""

            for edge in response_dict['edges']:

                node1_text = edge[0]
                node2_text = edge[1]
                edge_text = edge[2]

                # graph.add_node(pydot.Node(node1_text))
                # graph.add_node(pydot.Node(node2_text))
                # graph.add_edge(pydot.Edge(node1_text, node2_text, label=edge_text))

                dot_lang_start += f'\n    "{node1_text}" -> "{node2_text}" [label="{edge_text}"];'

            dot_lang_start += "\n}"

            print(dot_lang_start)
            #graph.write_png('graph.png', prog=["neato", "-overlap=scale", "-Gsplines=true", "-Gsep=+10", "-Gnodesep=+10", "-Gdpi=300"])
            # graph.write_png(os.path.join("static", infographic_id + ".png"), prog=["neato", '-x'], format = "png")
            graph = pydot.graph_from_dot_data(dot_lang_start)[0]
            infographic_path = os.path.join("static", infographic_id + ".png")
            graph.write(infographic_path, prog=["dot", "-Kneato"], format = "png")

            return graph, "http://127.0.0.1:7000/static/" + infographic_id + ".png"

        elif plot_type == "timeline":
            return self.create_timeline_infographic(response_dict)

        else:
            raise ValueError("Invalid plot_type")

    def create_timeline_infographic(self, timeline_dict):

        print(timeline_dict)

        x_len = len(timeline_dict['events'])
        y_axis = [1 for e in range(x_len)]
        
        fig = go.Figure([go.Scatter(x=timeline_dict['dates'], y=y_axis, text=timeline_dict['events'], textposition="bottom center" , mode='lines+markers')])

        ay_lst = [30,120,90,60,180,150]
        flag = 0

        for itr in range(x_len):
            if itr%2 == 0:
                fig.add_annotation(
                    xref="x domain",
                    yref="y domain",
                    # The arrow head will be 25% along the x axis, starting from the left
                    x=(itr+1)/x_len,
                # The arrow head will be 40% along the y axis, starting from the bottom
                    y=0.5,
                    ay=ay_lst[flag],
                    #yshift=-100,
                    text=timeline_dict['events'][itr],
                    arrowhead=2,
                    #textangle=-90
                )
            else:
                
                fig.add_annotation(
                    xref="x domain",
                    yref="y domain",
                    # The arrow head will be 25% along the x axis, starting from the left
                    x=(itr+1)/x_len,
                    # The arrow head will be 40% along the y axis, starting from the bottom
                    y=0.5,
                    ay=-ay_lst[flag],
                    #yshift=100,
                    text=timeline_dict['events'][itr],
                    arrowhead=2,
                    #textangle=-90
                )
                if flag == 5:
                    flag = 0
                else:
                    flag+=1

        infographic_id = str(uuid.uuid4())
        infographic_path = os.path.join("static", infographic_id + ".png")
        fig.write_image(infographic_path)

        return fig, "http://127.0.0.1:7000/static/" + infographic_id + ".png"

    
if __name__ == "__main__":

    input_text = """Higher income and good education helps students build a strong network and in-demand skills, which in turn builds a higher capacity to generate income. This leads to higher security cover from health and economic risks. With higher security the ability to pay off debt increases, which in turn leads to higher income.
"""
    
    plot_type = "graph"

    regenerator = Regenerate()
    response_text = regenerator(input_text, plot_type)
    print(response_text)