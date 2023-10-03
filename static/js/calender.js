let month_input = document.querySelector('#month')

todayDate()
startCalender()

month_input.addEventListener('change', () => {
    startCalender()
})

function startCalender() {
    let year = 2023;
    let month = (month_input.value.split('-'))[1]; // jan == 1, feb == 2

    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    let num_Of_days = new Date(year, month, 0).getDate() // num of days in this month
    let start_month_day = new Date(year, month-1, 1).getDay() // startCalender day name of in this month
    let last_month_day = new Date(year, month-1, num_Of_days).getDay() // last day name of in this month

    generateCalander(start_month_day, num_Of_days)
}


function todayDate(){
    let month_name = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    let month = document.querySelector('.head-month') //May - 2023
    let day = document.querySelector('.head-day')
    let date = new Date()
    month.innerHTML = `${month_name[date.getMonth()]} - ${date.getFullYear()}`
    day.innerHTML = `${date.getDate()}`
    month_input.setAttribute('max', `${date.getFullYear()}-0${date.getMonth()+1}`)
    month_input.setAttribute('min', `${date.getFullYear() - 4}-0${date.getMonth()}`)
    month_input.setAttribute('value', `${date.getFullYear()}-0${date.getMonth()+1}`)
}


function generateCalander(start_month_day, num_Of_days) {
    let arr_p = [5, 10, 12, 14]
    let arr_a = [15, 17, 19, 20]
    let arr_h = [1, 4, 11, 13]
    
    let p = 0
    let a = 0
    let h = 0
    let skip = 0
    let date;
    let box = "<tr id='tr_disable'>"
    let calender = document.querySelector('#calendar_body')
    calender.innerHTML = ""
    for (date = 0; date < num_Of_days; date++) {
        if(date%7 == 0){
            box = box + "</tr><tr>"
        }
        if (date >= start_month_day) {
            if (arr_p[p] == (date - skip + 1)) {
                p++;
                td = `<td persent='1' >${date - skip + 1}</td>`
            }
            else if(arr_a[a] == (date - skip + 1)){
                a++;
                td = `<td absent='1' >${date - skip + 1}</td>`
            }
            else if(arr_h[h] == (date - skip + 1)){
                h++;
                td = `<td holiday='1' >${date - skip + 1}</td>`
            }
            else{
                td = `<td open='1' >${date - skip + 1}</td>`
            }
            box = box + td;
        }
        else{
            td = "<td id='disabled' class=''></td>"
            box = box + td;
            skip++;
        }
    }

    if ((date - skip) < num_Of_days) {

        for (let index = 1; index <= skip; index++) {

            if((date+index-1)%7 == 0){
                box = box + "</tr><tr>"
            }

            // td = `<td id='' class=''>${(date - skip) + index}</td>`

            if (arr_p[p] == (date - skip + index)) {
                p++;
                td = `<td persent='1' >${date - skip + index}</td>`
            }
            else if(arr_a[a] == (date - skip + index)){
                a++;
                td = `<td absent='1' >${date - skip + index}</td>`
            }
            else if(arr_h[h] == (date - skip + index)){
                h++;
                td = `<td holiday='1' >${date - skip + index}</td>`
            }
            else{
                td = `<td open='1' >${date - skip + index}</td>`
            }
            box = box + td;
        }
    }
    box = box + "</tr>";
    calender.innerHTML = box
}
