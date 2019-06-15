frappe.provide('void');

frappe.ui.form.on("Sales Order", {
	onload: function(frm) {
	    console.log('onload');

		frm.add_custom_button(__("Void Document"), function (frm) {

			frappe.confirm(
    'Are you sure you want to cancel this Document?',
    function(){
        	console.log('HELLO HI');
			  frappe.call({
				  method: "void.void.void_so",
				  args: {
					  "docname": cur_frm.doc.name
				  },
				  callback: function (r) {
				  	console.log(r);
					  window.location.reload();
				  }
			  });
    },
    function(){
        // show_alert('Thanks for continue here!')
    }
)



		}).addClass("btn-primary")
    }
});