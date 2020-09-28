from anytree import Node, RenderTree,LevelOrderGroupIter
from anytree.exporter import DotExporter
from tkinter import *
from PIL import Image, ImageTk
from tkinter.ttk import Label as l
import pydot
from subprocess import call
import os
import zipfile


dirpath = os.getcwd()
os.environ["PATH"] += os.pathsep + dirpath + os.pathsep + 'release\\bin'


id_index=0
const_index=0
repeat_index=0
assign_index=0
op_index=0
write_index=0
read_index=0
if_index=0
stmt_sequence_index=-1
cluster_index=0
token=''
description=''
main = Tk()
#main.geometry("500x500")
v = IntVar()

path=Text(main,height=1,wrap=WORD)
path.grid(row=3)


def draw_file_path():
    if v.get() == 1:
        path.configure(height=1)
    elif v.get() == 2:
        path.config(height=20)
    return

def scanner(code):

    tiny_dict = {
        "reserved_words": (
            "if", "then", "else",
            "repeat", "read", "write",
            "until", "end"),
        "symbols": ("/", ":=", "+", "-", "^", "*", "=", "<", ">","(",")")
    }

    # function that takes a token and return the token + its id

    def id_token(token):

        if len(token) > 0:
            if token in tiny_dict["reserved_words"]:
                return token + ",Reserved Word"
            elif token in tiny_dict["symbols"]:
                return token + ",Symbol"
            # in case no spaces were left between operations
            for operator in tiny_dict["symbols"]:
                operator_index = token.find(operator)
                if operator_index == 0:
                    return operator + ",Symbol\r\n" + id_token(token[operator_index + len(operator):])
                elif operator_index == len(token) - 1:
                    return id_token(token[0:operator_index]) + "\r\n" + operator + ",Symbol"
                elif operator_index > 0:
                    return id_token(token[0:operator_index]) + "\r\n" + operator + ",Symbol\r\n" + id_token(
                        token[operator_index + len(operator):])

            if token[0].isdigit():
                return token + ",Number"
            else:
                return token + ",Identifier"
        else:
            return ""

    # getting rid of comment contents first
    begin = 0
    braces_count = code.count("{")

    for i in range(1, braces_count + 1):
        comment_start = code.find('{', begin)
        begin = comment_start + 1
        comment_end = code.find('}', comment_start)
        code = code[0:comment_start] + code[comment_end + 1:]

    code_split_semicolon = code.split(";")
    output = ""
    for line in code_split_semicolon:
        if len(line) > 0:
            split_line = line.split()
            for token in split_line:
                if len(token) > 0:
                    output+=id_token(token) + "\r\n"
            if line != code_split_semicolon[-1]:
                output+=";,symbol\r\n"

    tokenlines=output.splitlines()


    return tokenlines


def parser(lines):
    global token,description,cluster_index,stmt_sequence_index
    stmt_sequence_index=0
    cluster_index=0
    [token, description] = lines[0].split(",")
    graph = pydot.Dot(graph_type='digraph', rankdir="TB")
    def match(text):

        global token, description
        if text == "number" or text == "identifier":
            if description.lower() == text:
                del lines[0]
                if len(lines)>0:
                    [token, description] = lines[0].split(",")
                return True
            else:
                return False
        else:
            if token == text:
                del lines[0]
                if len(lines) > 0:
                    [token, description] = lines[0].split(",")
                return True
            else:
                return False

    def repeat_stmt():
        global token, description
        global repeat_index
        if token == "repeat":
            match("repeat")
            stmt_sequence_repeat = stmt_sequence()
            match("until")
            exp_node = exp()
            repeat_node = Node("repeat" + str(repeat_index))
            repeat_index += 1
            stmt_sequence_repeat.parent = repeat_node
            exp_node.parent = repeat_node
            return repeat_node

    def assign_stmt():
        global token, description
        global assign_index, id_index
        if description.lower() == "identifier":
            assign_node = Node("assign" + str(assign_index))
            assign_index += 1
            id_node = Node("id" + str(id_index) + "\n(" + token + ")", parent=assign_node)
            id_index += 1
            match("identifier")
            match(":=")
            exp_node = exp()
            exp_node.parent = assign_node
            return assign_node

    def term():
        global token, description
        global op_index
        temp = factor()

        while token == "*":
            newtemp = Node("op" + str(op_index) + "\n" + token)
            op_index += 1
            match(token)
            temp.parent = newtemp
            factor().parent = newtemp
            temp = newtemp
        return temp

    def factor():
        global token, description
        global const_index, id_index
        if token == "(":
            match("(")
            temp=exp()
            match(")")
            return temp
        elif description.lower() == "number":
            temp = Node("Const" + str(const_index) + "\n(" + token + ")")
            const_index += 1
            match("number")
            return temp

        elif description.lower() == "identifier":
            temp = Node("Id" + str(id_index) + "\n(" + token + ")")
            id_index += 1
            match("identifier")
            return temp
        else:
            return

    def write_stmt():
        global token, description, write_index
        match("write")
        temp = Node("Write" + str(write_index))
        write_index += 1
        exp().parent = temp
        return temp

    def read_stmt():
        global token, description, read_index, id_index
        match("read")
        temp = Node("Read" + str(read_index))
        read_index += 1
        newtemp = Node("Id" + str(id_index) + "\n(" + token + ")", parent=temp)
        id_index += 1
        match("identifier")
        return temp

    def stmt_sequence():
        global token, description, stmt_sequence_index
        temp = Node("stmt_sequence" + str(stmt_sequence_index) + "\n")
        stmt_sequence_index += 1
        statement().parent = temp

        while token == ";":
            match(token)
            statement().parent = temp

        return temp

    def simple_exp():
        global token, description, op_index
        temp = term()

        while (token == "+" or token == "-"):
            newtemp = Node("op" + str(op_index) + "\n" + token)
            op_index += 1
            match(token)
            temp.parent = newtemp
            term().parent = newtemp
            temp = newtemp
        return temp

    def exp():
        global token, description, op_index
        temp = simple_exp()

        while (token == "<" or token == ">" or token == "=" or token == "!="):
            newtemp = Node("op" + str(op_index) + "\n" + token)
            op_index += 1
            match(token)
            temp.parent = newtemp
            simple_exp().parent = newtemp
            temp = newtemp
        return temp

    def if_stmt():
        global token, description, if_index
        temp = Node("if" + str(if_index))
        if_index += 1
        match("if")
        match("(")
        exp().parent = temp
        match(")")
        match("then")
        stmt_sequence().parent = temp
        if token == "else":
            match("else")
            stmt_sequence().parent = temp
        match("end")
        return temp

    def statement():
        global token, description
        if token == "if":
            return if_stmt()
        elif token == "repeat":
            return repeat_stmt()
        elif description.lower() == "identifier":
            return assign_stmt()
        elif token == "read":
            return read_stmt()
        elif token == "write":
            return write_stmt()

    def draw_edges(root):
        if "stmt_sequence" in root.name:
            edge = pydot.Edge(root.parent.name, root.children[0].name)
            graph.add_edge(edge)
            for x in range(0, len(root.children) - 1):
                edge = pydot.Edge(root.children[x].name, root.children[x + 1].name, dir='none')
                graph.add_edge(edge)
            for i in root.children:
                draw_edges(i)
        else:
            for i in root.children:
                if "stmt_sequence" not in i.name:
                    edge = pydot.Edge(root.name, i.name)
                    graph.add_edge(edge)
                draw_edges(i)
        return

    start_node = Node("Start")
    stmt_sequence().parent = start_node
    cluster1 = pydot.Subgraph("level" + str(cluster_index), rank="same")
    cluster_index += 1
    # cluster1.add_node(pydot.Node(node.name))

    # subgraphs=[[node.name for node in children] for children in LevelOrderGroupIter(start_node)]
    subgraphs = []
    for children in LevelOrderGroupIter(start_node):
        childrenss = []
        for node in children:
            if "stmt_sequence" in node.name:
                for inner_child in node.children:
                    childrenss.append(inner_child.name)
            else:
                if len(subgraphs) == 0:
                    childrenss.append(node.name)
                elif node.name not in subgraphs[-1]:
                    childrenss.append(node.name)
        if len(childrenss) > 0:
            subgraphs.append(childrenss)

    for sub in subgraphs:
        for i in sub:
            if "stmt_sequence" in i:
                continue
            cluster1.add_node(pydot.Node(i))
        graph.add_subgraph(cluster1)
        cluster1 = pydot.Subgraph("level" + str(cluster_index), rank="same")
        cluster_index += 1
    draw_edges(start_node)
    graph.write('p2.txt')
    cmd = ["dot", 'p2.txt', "-T", 'png', "-o", 'Parser.png']
    call(cmd)
    return

def generate_syntax_tree():
    if v.get() == 1:
        file_path=path.get("1.0",END).replace('\n','')

        x=open(file_path,'r')
        code=x.read()


    elif v.get() == 2:
        code=path.get("1.0",END)

    lines = scanner(code)
    parser(lines)

    main.destroy()

    return
main.title("Parser")
Label(main, text="Choose input Method",justify=LEFT).grid(row=0,column=0)
Radiobutton(main,text="File",variable=v,value=1,command=draw_file_path).grid(row=1,column=0)
Radiobutton(main,text="Code",variable=v,value=2,command=draw_file_path).grid(row=2,column=0)
Button(main,text="Generate Tree",command=generate_syntax_tree).grid(row=25)

main.mainloop()



class ScrolledCanvas(Frame):
    def __init__(self, parent=None):
        Frame.__init__(self, parent)
        self.master.title("Syntax Tree")
        self.pack(expand=YES, fill=BOTH)
        canv = Canvas(self, relief=SUNKEN)
        canv.config(width=1100, height=500)
        # canv.config(scrollregion=(0,0,1000, 1000))
        # canv.configure(scrollregion=canv.bbox('all'))
        canv.config(highlightthickness=0)

        sbarV = Scrollbar(self, orient=VERTICAL)
        sbarH = Scrollbar(self, orient=HORIZONTAL)

        sbarV.config(command=canv.yview)
        sbarH.config(command=canv.xview)

        canv.config(yscrollcommand=sbarV.set)
        canv.config(xscrollcommand=sbarH.set)

        sbarV.pack(side=RIGHT, fill=Y)
        sbarH.pack(side=BOTTOM, fill=X)

        canv.pack(side=LEFT, expand=YES, fill=BOTH)
        self.im = Image.open("Parser.png")
        width, height = self.im.size
        canv.config(scrollregion=(0, 0, width, height))
        self.im2 = ImageTk.PhotoImage(self.im)
        self.imgtag = canv.create_image(0, 0, anchor="nw", image=self.im2)


ScrolledCanvas().mainloop()
os.remove("Parser.png")
