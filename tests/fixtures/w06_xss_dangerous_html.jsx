import React from 'react';

export function CommentBody({ comment }) {
  return <div className="comment" dangerouslySetInnerHTML={{ __html: comment.body }} />;
}

export function renderBio(el, bio) {
  el.innerHTML = bio;
}
