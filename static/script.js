const url = window.location.origin + window.location.pathname.split('index.html')[0]

// open sidebar

const sidebar = document.querySelector('.main__content__sidebar')
const sidebar_button = document.querySelector('.header__action_new')
const main__content_container = document.querySelector('.main__content_container')
sidebar_button.onclick = function() { sidebar.classList.toggle('open'); main__content_container.classList.toggle('open'); }


// delete 

const delete_message = function(key) {
    fetch(url + 'api/delete', {
        method: 'DELETE',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({key: key})
      })
        .then(response => response.json())
        .then(data => console.log(data))
        .catch(err => console.error(err));
    document.querySelector('[data-key="' + key + '"]').remove()
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM LOADED');
    const action_delete = document.querySelectorAll('.bottom_bar__action_delete');
    action_delete.forEach((item) => {
        let key = item.parentElement.parentElement.parentElement.getAttribute('data-key')
        item.addEventListener('click', function() { delete_message(key) })
    })
});
