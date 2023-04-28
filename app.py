from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

app = Flask(__name__)
app.secret_key = '1893'

#conn = sqlite3.connect('models/innmaster.db')
#con = conn.cursor()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/guest")
def guest():
    return render_template("guest.html")

@app.route("/guestlogin")
def guestlogin():
    return render_template("guestlogin.html")

@app.route("/auth_guest", methods=["POST"])
def auth_guest():
    guest_name = request.form["name"]
    guest_password = request.form["password"]
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("SELECT * FROM guests WHERE name=? AND password=?", (guest_name, guest_password))
        guest = con.fetchone()
        print(guest)
    if guest:
        session['user_id'] = guest[0]  # Set the user_id session variable to the guest's ID
        return redirect(url_for("guestdashboard"))
    else:
        return redirect(url_for("guestlogin"))

@app.route("/guestdashboard", methods=['GET', 'POST'])
def guestdashboard():
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("SELECT id, itemname, itemprice FROM menu")
        menu_items = con.fetchall()
        # Fetch room and guest details
        con.execute("SELECT room.id, room.price, guests.id, guests.balance, guests.bill FROM room JOIN guests ON room.guestid = guests.id WHERE guests.id=?", (session["user_id"],))
        rows = con.fetchall()

    return render_template("guestdashboard.html", menu_items=menu_items, rows=rows)

@app.route("/order_item", methods=['POST'])
def order_item():
    item_id = request.form['item_id']
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("SELECT itemprice FROM menu WHERE id=?", (item_id,))
        item_price = con.fetchone()[0]
        con.execute("UPDATE guests SET bill = bill + ? WHERE id=?", (item_price, session["user_id"]))
        conn.commit()
        flash("Item ordered successfully", "item-order-success")
        

    return redirect(url_for("guestdashboard"))

@app.route("/pay_bill", methods=['POST'])
def pay_bill():
    amount_paid = float(request.form['amount'])
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("SELECT balance, bill FROM guests WHERE id=?", (session["user_id"],))
        guest_info = con.fetchone()
        balance = guest_info[0]
        current_bill = guest_info[1]
        if amount_paid > current_bill:
            flash("Amount paid cannot be greater than the current bill", "amt-danger")
        elif amount_paid > balance:
            flash("Amount paid cannot be greater than the available balance", "danger")
        else:
            new_balance = balance - amount_paid
            new_bill = current_bill - amount_paid
            con.execute("UPDATE guests SET balance = ?, bill=? WHERE id=?", (new_balance, new_bill, session["user_id"]))
            conn.commit()
            flash("Bill updated successfully", "amt-success")

    return redirect(url_for("guestdashboard"))

@app.route("/roomtable", methods=["GET", "POST"])
def roomtable():
    # Get the list of available rooms
    #conn = sqlite3.connect('models/innmaster.db')
    #con = conn.cursor()
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("SELECT id, price FROM room WHERE availability = 0")
        rooms = con.fetchall()
        print(rooms)
    
    available_rooms = rooms
    room_list = []
    for room in available_rooms:
        room_dict = {}
        room_dict["id"] = room[0]
        room_dict["price"] = room[1]
        room_list.append(room_dict)

    # Render the booking form
    return render_template("bookroom.html", rooms=room_list)

@app.route("/bookroom", methods=["GET", "POST"])
def bookroom():
    # Get the list of available rooms
    #conn = sqlite3.connect('models/innmaster.db')
    #con = conn.cursor()
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("SELECT id, price FROM room WHERE availability = 0")
        rooms = con.fetchall()
        print(rooms)
    
    available_rooms = rooms
    room_list = []
    for room in available_rooms:
        room_dict = {}
        room_dict["id"] = room[0]
        room_dict["price"] = room[1]
        room_list.append(room_dict)
    
    if request.method == "POST":
        # Handle form submission
        room_ids = request.form.getlist("room_id[]")
        #print("printing room ids",room_ids)
        name = request.form["name"]
        #print(name)
        password = request.form["password"]
        #print(password)
        checkout = request.form["checkout"]
        #print(checkout)
        
        # Create a new bookingrequest in the database
        #conn = sqlite3.connect('models/innmaster.db')
        #co = conn.cursor()
        
        with sqlite3.connect('models/innmaster.db') as conn:
            con = conn.cursor()
            for rid in room_ids:
                con.execute("INSERT INTO roomrequests (roomid, guestname, checkoutdate, gpassword) VALUES (?, ?, ?, ?)", (rid, name, checkout, password))
            
            con.execute("SELECT * FROM roomrequests")
            result = con.fetchall()
            print(result)
            
        # Display a confirmation message to the user
        flash("Your booking has been submitted!", "booking-success")
        return redirect(url_for("bookroom"))
    # Render the bookroom template with the room information
    return render_template("bookroom.html", rooms=room_list)


@app.route("/adminlogin")
def adminlogin():
    return render_template("adminlogin.html")

@app.route("/auth_admin", methods=["POST"])
def auth_admin():
    #c = conn.cursor()
    admin_id = request.form["id"]
    admin_password = request.form["password"]
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("SELECT * FROM admin WHERE id=? AND password=?", (admin_id, admin_password))
        admin = con.fetchone()
        print(admin)
    if admin:
        return redirect(url_for("admindashboard"))
    else:
        return redirect(url_for("adminlogin"))

@app.route("/admindashboard", methods=['GET', 'POST'])
def admindashboard():
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("SELECT roomid, guestname, checkoutdate FROM roomrequests")
        room_requests = con.fetchall()
        print("here",room_requests)
        
        # Fetch current guests
        con.execute("SELECT guests.name, room.id, guests.id FROM guests JOIN room ON guests.id = room.guestid WHERE room.availability = 1")
        current_guests = con.fetchall()
        print(current_guests)
        
        # Fetch current menu items
        con.execute("SELECT id, itemname, itemprice FROM menu")
        current_menu = con.fetchall()
        #new
        if request.method == 'POST':
            room_id = request.form['room_id']
            guest_name = request.form['guest_name']
            checkout_date = request.form['checkout_date']
            
            con.execute("SELECT roomid, guestname, checkoutdate, gpassword FROM roomrequests WHERE roomid = ?",(room_id))
            roomreqs = con.fetchone()
            print(roomreqs)
            con.execute("SELECT price FROM room WHERE id = ?",(room_id))
            roomprice = con.fetchone()
            print(roomprice)
            
            con.execute("INSERT INTO guests (name, password) VALUES (?, ?)", (roomreqs[1], roomreqs[3]))
            
            con.execute("SELECT id, bill, balance FROM guests WHERE (name = ?) AND (password = ?)",(roomreqs[1], roomreqs[3]))
            gid = con.fetchone()
            print(gid)
            
            con.execute("UPDATE guests SET bill = ?, balance = ? WHERE id = ?", (gid[1]+roomprice[0], gid[2]-roomprice[0], gid[0]))
            
            con.execute("UPDATE room SET availability = ?, guestid = ? WHERE id = ?", (1, gid[0], room_id))
            con.execute("DELETE FROM roomrequests WHERE roomid = ?", (room_id,))
            conn.commit()

            flash('Room request accepted!', 'room-success')
            return redirect(url_for('admindashboard'))
        #end new

    return render_template("admindashboard.html", room_requests=room_requests, current_guests=current_guests, current_menu=current_menu)

@app.route("/rejectrequest", methods=['POST'])
def rejectrequest():
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        if request.method == 'POST':
            room_id = request.form['room_id']
            guest_name = request.form['guest_name']
            checkout_date = request.form['checkout_date']
            
            con.execute("DELETE FROM roomrequests WHERE roomid = ?",(room_id))
            roomreqs = con.fetchone()

            flash('Room request rejected!', 'room-success')
            return redirect(url_for('admindashboard'))
    
@app.route("/remove_guest", methods=['POST'])
def remove_guest():
    guest_id = request.form['guest_id']
    print(guest_id)
    
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        guest_id = request.form['guest_id']
        con.execute("UPDATE room SET availability = ?, guestid = NULL WHERE guestid = ?", (0, guest_id))
        con.execute("DELETE FROM guests WHERE id = ?", (guest_id,))
        conn.commit()

        flash('Guest removed!', 'guest-rmv-success')
        return redirect(url_for('admindashboard'))

@app.route("/remove_menu_item", methods=['POST'])
def remove_menu_item():
    item_id = request.form['item_id']
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("DELETE FROM menu WHERE id = ?", (item_id,))
        conn.commit()
        flash('Menu item removed!', 'item-success')
    return redirect(url_for('admindashboard'))

@app.route("/add_menu_item", methods=['POST'])
def add_menu_item():
    item_name = request.form['itemname']
    print(item_name)
    item_price = request.form['itemprice']
    print(item_price)
    with sqlite3.connect('models/innmaster.db') as conn:
        con = conn.cursor()
        con.execute("INSERT INTO menu (itemname, itemprice) VALUES (?, ?)", (item_name, item_price))
        conn.commit()
        flash('New menu item added!', 'item-success')
    return redirect(url_for('admindashboard'))

if __name__ == "__main__":
    app.run(debug=True)
