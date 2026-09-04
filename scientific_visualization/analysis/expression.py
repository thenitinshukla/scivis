from __future__ import annotations
import ast
import numpy as np
from ..core.data import Dataset
from .derived import DerivedQuantityEngine
from ..physics import PhysicsEngine

_ALLOWED_BIN = (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
_ALLOWED_UNARY = (ast.UAdd, ast.USub)

class SafeExpressionEngine:
    """Small AST-based expression evaluator for Dataset arithmetic.

    No unrestricted eval is used. Names resolve only to supplied datasets or approved functions.
    """
    def __init__(self):
        self.derived = DerivedQuantityEngine()
        self.physics = PhysicsEngine()

    def evaluate(self, expression: str, datasets: dict[str, Dataset], name: str|None=None) -> Dataset:
        tree = ast.parse(expression, mode="eval")
        ds = self._eval(tree.body, datasets)
        if not isinstance(ds, Dataset):
            raise ValueError("Expression must produce a Dataset")
        ds.name = name or ds.name
        return ds

    def _eval(self, node, env):
        if isinstance(node, ast.Name):
            if node.id not in env: raise ValueError(f"Unknown quantity '{node.id}'")
            return env[node.id]
        if isinstance(node, ast.Constant) and isinstance(node.value,(int,float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op,_ALLOWED_UNARY):
            a=self._eval(node.operand,env)
            if isinstance(a,Dataset):
                data = a.data if isinstance(node.op,ast.UAdd) else -a.data
                return Dataset(a.name,data,a.axes,a.coordinates,a.units,a.time,a.time_units,{**dict(a.metadata),"expression":True},a.source,a.simulation_metadata,derived_from=(a.name,))
            return +a if isinstance(node.op,ast.UAdd) else -a
        if isinstance(node, ast.BinOp) and isinstance(node.op,_ALLOWED_BIN):
            a,b=self._eval(node.left,env),self._eval(node.right,env)
            return self._binary(a,b,node.op)
        if isinstance(node, ast.Call):
            if not isinstance(node.func,ast.Name): raise ValueError("Only direct function calls are allowed")
            fn=node.func.id
            if fn in {"sqrt","abs","log","log10"} and len(node.args)==1:
                a=self._eval(node.args[0],env)
                if not isinstance(a,Dataset): raise ValueError(f"{fn} requires a Dataset")
                func={"sqrt":np.sqrt,"abs":np.abs,"log":np.log,"log10":np.log10}[fn]
                return Dataset(f"{fn}({a.name})",func(a.data),a.axes,a.coordinates,a.units,a.time,a.time_units,{"expression":fn},a.source,a.simulation_metadata,derived_from=(a.name,))
            if fn in {"magnitude", "div", "curl"}:
                return self._vector_call(node.args,env,operation=fn)
            if fn in {"gradient","integrate","average"} and len(node.args)==2:
                a=self._eval(node.args[0],env); axis=self._literal(node.args[1])
                return getattr(self.derived,fn)(a,axis)
            raise ValueError(f"Function '{fn}' is not permitted")
        raise ValueError(f"Unsupported expression element: {type(node).__name__}")

    def _vector_call(self,args,env,operation="magnitude"):
        if len(args)!=1 or not isinstance(args[0],ast.Name): raise ValueError("magnitude(E) requires a component prefix name")
        prefix=args[0].id
        comps={k[1:]:v for k,v in env.items() if k.startswith(prefix) and k[len(prefix):] in {"1","2","3"}}
        if not comps: raise ValueError(f"No components found for {prefix}")
        if operation == "magnitude":
            return self.derived.vector_magnitude(comps,name=f"|{prefix}|")
        if operation == "div":
            return self.physics.divergence(comps, name=f"div({prefix})")
        if operation == "curl":
            raise ValueError("curl(B) is available through PhysicsEngine.curl; use a 3-component Dataset mapping in the Python API")

    def _literal(self,node):
        if isinstance(node,ast.Constant) and isinstance(node.value,(str,int)): return node.value
        if isinstance(node,ast.Name): return node.id
        raise ValueError("Expected an axis literal")

    def _binary(self,a,b,op):
        if isinstance(a,Dataset) and isinstance(b,Dataset):
            if a.shape!=b.shape or a.axes!=b.axes: raise ValueError("Datasets must have compatible shapes and axes")
            data = {ast.Add:a.data+b.data,ast.Sub:a.data-b.data,ast.Mult:a.data*b.data,ast.Div:np.divide(a.data,b.data),ast.Pow:a.data**b.data}[type(op)]
            return Dataset("derived",data,a.axes,a.coordinates,a.units,a.time,a.time_units,{"expression":type(op).__name__},a.source,a.simulation_metadata,derived_from=(a.name,b.name))
        if isinstance(a,Dataset): data={ast.Add:a.data+b,ast.Sub:a.data-b,ast.Mult:a.data*b,ast.Div:np.divide(a.data,b),ast.Pow:a.data**b}[type(op)]; return Dataset(a.name,data,a.axes,a.coordinates,a.units,a.time,a.time_units,{"expression":True},a.source,a.simulation_metadata,derived_from=(a.name,))
        if isinstance(b,Dataset): data={ast.Add:a+b.data,ast.Sub:a-b.data,ast.Mult:a*b.data,ast.Div:np.divide(a,b.data),ast.Pow:a**b.data}[type(op)]; return Dataset(b.name,data,b.axes,b.coordinates,b.units,b.time,b.time_units,{"expression":True},b.source,b.simulation_metadata,derived_from=(b.name,))
        return {ast.Add:a+b,ast.Sub:a-b,ast.Mult:a*b,ast.Div:a/b,ast.Pow:a**b}[type(op)]
