# Welcome to ORMStorm

ORMStrom is a small library for easy work with databases.

## The key features are:

 - **Simplicity:** The library is very simple and it won't take long to learn it.
 - **Coding speed:** Integrating the library into your projects won't take long.
 - **Dynamic:** Unlike others, this library will allow you to very quickly create new tables and add databases to them.

## Installing

    pip install ormstorm
   
## Usage

Using standard tables

```python
from ormstorm import Table, Types, Column, create_session  
  
  

class ExampleTable(Table): 
    __tablename__ = "example"  
      
    id = Column(Types.INTEGER, primary_key=True, autoincrement=True)  
    text = Column(Types.STRING)  
      
      
LocalSession = create_session("example.sqlite3", [ExampleTable])  
      
with LocalSession() as session:  
    session.insert(ExampleTable(text="Hello, world!"))
```

Using a dynamic table

```python
from ormstorm import DynamicTable, Types, Column, create_session  
      
      
LocalSession = create_session("example.sqlite3", [])  
      
with LocalSession() as session:  
    NewTable = DynamicTable(  
        "new_table", {"id": Column(Types.INTEGER, primary_key=True, autoincrement=True), "text": Column(Types.STRING)}  
    )  
      
    session.create(NewTable)  
    session.insert(NewTable(text="Easy use of dynamic tables!"))
```

## Note

This library is strictly not recommended for use in large projects because of the small functionality!
